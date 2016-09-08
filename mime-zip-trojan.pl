#!/usr/bin/perl
#
# Fork of the original script available on: https://www.dirwiz.com/news/276
#
# Added support for more suspicious extensions and checking all files in the
# zip file
#

use File::Temp;
use Archive::Zip qw( :ERROR_CODES :CONSTANTS );
use MIME::Parser;

sub has_trojan_zip
{
        $head=$_[0]->head;
        if ($head->recommended_filename=~/\.zip$/i)
        {
                $fh=File::Temp->new();
                $fname=$fh->filename;
                open FILE,">",$fname || die $!;
                print FILE $_[0]->bodyhandle->as_string;
                close FILE;

                my $zip=Archive::Zip->new($fname);
                @members=$zip->memberNames;
                for ($i=0; $i < $zip->numberOfMembers; $i++)
                {
                        return 1 if $members[$i]=~/\.(chm|scr|doc|js|exe|wsf|jar|hta|pub|vba|vbs)$/i;
                }
        }
        return 0;
}

my $parser = new MIME::Parser;
$parser->output_to_core(1);
$entity=$parser->parse(\*STDIN) or die "parse failed";

my $flag=0;
foreach my $part ($entity->parts)
{
        $flag=1 if has_trojan_zip($part)==1;
}

$head=$entity->head;
$head->add('X-Zip-Trojan','Yes') if $flag==1;

$entity->print(\*STDOUT);
