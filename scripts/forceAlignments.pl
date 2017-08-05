#!/usr/bin/perl
use strict;
#use warnings FATAL => 'all';
use Data::Dumper qw(Dumper);
no warnings 'recursion';

#######Sys arguments ############
my $book_id = $ARGV[0];
my $chapter_id = $ARGV[1];
my $reader_id = $ARGV[2];
my $corpus = $ARGV[3];

### Input / Output #########

# Puncts !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
my $transcpt = "../Alignements/data/$book_id/data/$chapter_id/$reader_id-$chapter_id.trans.txt";
open(my $fh_tcpt , '<:encoding(UTF-8)', $transcpt)
  or die "Could not open file '$transcpt' $!";
my $count_transcription= `cat $transcpt | wc -l`;


my $book = "../Alignements/data/$book_id/Alignments/$chapter_id/reversed_stem_ls.txt";
open(my $fh_book , '<:encoding(UTF-8)', $book)
  or die "Could not open file '$book' $!";

my $scores = "../Alignements/data/$book_id/Alignments/$chapter_id/scores.txt";
open(my $fh_scores , '<:encoding(UTF-8)', $scores)
  or die "Could not open file '$scores' $!";

my $sortie = "../Alignements/data/$book_id/Alignments/$chapter_id/final.txt";
open(my $fh_sortie , '>:encoding(UTF-8)', $sortie)
  or die "Could not open file '$sortie' $!";

my $translation = "../Alignements/data/$book_id/Alignments/$chapter_id/reversed_stem_lc.txt";
open(my $fh_translation , '<:encoding(UTF-8)', $translation)
  or die "Could not open file '$translation' $!";


my %lines;
while (my $line = <$fh_book>){
    chomp $line;
    $line =~ /<(\d+)>(.+?)<\d+>/;
    $lines{$1} = $2
}

my %scores;
while (my $line = <$fh_scores>){
    chomp $line;
    $line =~ /<(\d+)>(.+?)<\d+>/;
    $scores{$1} = $2
}

my %translations;

while (my $line = <$fh_translation>){
    chomp $line;
    $line =~ /<(\d+)>(.+?)<\d+>/;
    $translations{$1} = $2;
}

if ($corpus eq 'dev'){
    my $lineCount = 0;
    while (my $row = <$fh_tcpt>) {
        chomp $row;
        #print($row);
        $row =~ s/(\d+-\d+-\d+) (.*)/$2/gm;
        my $id_phrase = $1;

        my @charsRef = split(//,lc($row));
        my $maxScore = 0;
        my $associated = 0;
        print("Comparing line: $lineCount with " . scalar(keys %lines) . " sents recursively!\n");
        for my $key ( sort {$a<=>$b} keys %lines) {
               #print "($key)->($lines{$key})\n";
                my @charsHyp = split(//, lc($lines{$key}));
                my $scmTab = [];
                 my $score = maxSubString(0,0,\@charsRef,\@charsHyp, $scmTab);

                my $difference;
                if (length($row) > length($lines{$key})){
                    $difference = (length($row) - length($lines{$key}))
                }else{
                    $difference = (length($lines{$key}) - length($row))
                }

               # print("\t\t". $difference . "\n");
                if (($score > $maxScore) && ($difference <20)){
                    $maxScore = $score;
                    $associated = "<$key> $lines{$key} <$key>";
                }
        }

        print("\t\t\t$translations{$id_phrase}");
        $associated =~ /<(\d+)>.+?<\d+>/;
        print("\tLine: $lineCount / $count_transcription");

        print $fh_sortie "<$id_phrase> $row <$id_phrase>\t$associated\t<$1> $translations{$1} <$1>\t$scores{$1}\n";
        $lineCount++;
    }
}else{
    my $lineCount = 0;
    while (my $row = <$fh_tcpt>){
        chomp($row);

        $row =~ s/(\d+-\d+-\d+) (.*)/$2/gm;
        my $id_phrase = $1;
        #print("$row\n");

        my @charsRef = split(//,lc($row));
        my $maxScore = 0;
        my $associated = 0;

       # print("Comparing line: $lineCount with " . scalar(keys %lines) . " sents recursively!\n");
         for my $key ( sort {$a<=>$b} keys %lines){
             #print(length($row) ."\t" . length($lines{$key})."\n");

             my $phrase = $lines{$key};

             if(length($row) > length($phrase))
             {

                 while( length($phrase)  < length($row) )
                 {
                    $phrase .= $lines{$key+1};

                 }
                  #print($phrase ."\n");
                  my @charsHyp = split(//, lc($phrase));
                  my $scmTab = [];
                  my $score = maxSubString(0,0,\@charsRef,\@charsHyp, $scmTab);

                  if ($score > $maxScore)
                   {
                    $maxScore = $score;
                    $associated = "<$key> $phrase <$key>";
                    }

             }else{
                  my @charsHyp = split(//, lc($lines{$key}));
                  my $scmTab = [];
                  my $score = maxSubString(0,0,\@charsRef,\@charsHyp, $scmTab);
                  if ($score > $maxScore)
                   {
                    $maxScore = $score;
                    $associated = "<$key> $phrase <$key>";
                    }
             }


              #print($phrase)
         }
        $associated =~ /<(\d+)>.+?<\d+>/;
        print("\tLine: $lineCount / $count_transcription");

        print  $sortie "<$id_phrase> $row <$id_phrase>\t$associated\t<$1> $translations{$1} <$1>\t$scores{$1}\n";
        $lineCount++;
    }

}





#Renvoie la longueur de la plus longue sous chaîne max entre les
#tableaux de car. $l1 et $l2, à partir des coordonnées ($i,$j) - les
#longueurs déjà calculées étant stockées dans le tableau $scmTab.
# Au premier appel on fait donc : $scmTab=[];
#$scm=maxSubString(0,0,split(//,$string1),split(//,$string2),$scmTab)

sub maxSubString {
     my ($i,$j,$l1,$l2,$scmTab)=@_;
     my $diffMaxSCM;
     # la récursivité s'arrête si un des deux indices arrive en fin de
#tableau
     if (($i==@{$l1}) || ($j==@{$l2}) )  {
         return 0;
     }
     # si l'écart entre $i et $j est supérieur Ã  $diffMax, fin de la
#récursivité

     if ($diffMaxSCM && abs($i-$j)>$diffMaxSCM) {
         return 0;
     }

     # si la valeur a déjà été calculé lors d'un précéent appel, on ne
#refait pas le calcul
     if (defined($scmTab->[$i]) && defined($scmTab->[$i][$j])) {
         return $scmTab->[$i][$j];
     }

     # récursivité selon $i
     my $tete1 = $l1->[$i];
     my $index=-1;
     for (my $k=$j;$k<@{$l2};$k++) {
         if ($l2->[$k] eq $tete1) {
             $index=$k;
             last;
         }
     }

     # initialisation de $SCM[$i+1]
     if (!defined($scmTab->[$i+1])) {
         $scmTab->[$i+1]=[];
     }

      # s'il n'y a pas d'occurrence de la $tete1 dans @sent2[$j..n]
     if ($index == -1) {
         my $length=maxSubString($i+1,$j,$l1,$l2,$scmTab);
         $scmTab->[$i+1][$j]=$length;
         return $length;
     } else {
         # premier calcul : on tient compte du matching de $tete1, et on
#relance le calcul récursivement pour les listes restante
         my $length1= maxSubString($i+1,$index+1,$l1,$l2,$scmTab);
         $scmTab->[$i+1][$index+1]=$length1;

         # deuxième calcul : on ne tient pas compte du matching de
#tête1, et on relance le calcul pour $i+1,$j
         my $length2 = maxSubString($i+1,$j,$l1,$l2,$scmTab);
         $scmTab->[$i+1][$j]=$length2;

         # on valide le meilleur des deux chemins
         if ($length1+1 >= $length2) {
             return $length1+1;
         } else {
             return $length2;
         }
     }
}
