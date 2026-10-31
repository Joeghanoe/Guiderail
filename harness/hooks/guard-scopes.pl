#!/usr/bin/perl
# Splits a Bash command into the parts guard-bash.sh checks differently (SEC.2). The command is read from stdin.
#   guard-scopes.pl shell    the command as a shell would run it: what the broad checks scan
#   guard-scopes.pl interp   the bodies of heredocs fed to a non-shell interpreter (python, node, perl ...): what the narrow checks scan
#
# Why: a heredoc body is not always code. The old guard scanned all of it for words, so a C# `{ get; set; }`, a dotenv path or
# `process.env` in a comment, or "tofu" in a recipe blocked a harmless `cat > file <<EOF`, and a script that only mentions those
# words could be written no other way than through the Write tool. A heredoc is classified by the line that introduces it:
#   fed to a shell (bash, sh, source, eval, ssh ...), to `$(...)` or backticks, or piped to something unknown  -> shell scope, scanned in full
#   fed to a script interpreter (python, node, perl, ruby, pwsh ...)                                          -> interp scope, narrow checks
#   anything else (cat > f, tee f, a read loop)                                                               -> file content, dropped
# The introducing line itself always stays in the shell scope, so `cat > .harness/x <<EOF` is still caught (H.1).
# Quoted arguments of prose flags (-m, --message, --body, --title, --notes) and of echo or printf are also dropped.
use strict;
use warnings;

my $mode = shift // 'shell';
local $/;
my $command = <STDIN> // '';
my @lines = split /\n/, $command, -1;
my (@shell, @interp);

my $SHELLISH = qr/\b(?:bash|sh|zsh|dash|ksh|fish|source|eval|ssh|sudo|su|xargs|exec)\b/;
my $SCRIPTISH = qr/\b(?:python3?|node|nodejs|bun|deno|perl|ruby|php|lua|pwsh|powershell|osascript|rscript)\b/;

my $i = 0;
while ($i < @lines) {
    my $line = $lines[$i++];
    push @shell, $line;
    my @tags;
    while ($line =~ /(?<!<)<<(-?)[ \t]*(["']?)(\w+)\2/g) { push @tags, [$1, $3]; }
    next unless @tags;

    my $kind =
        $line =~ $SHELLISH ? 'shell'
      : $line =~ /\$\(|`/ ? 'shell'
      : $line =~ $SCRIPTISH ? 'interp'
      : $line =~ /\|/ ? 'shell'
      : 'data';

    for my $tag (@tags) {
        my ($dash, $word) = @$tag;
        my @body;
        while ($i < @lines) {
            my $candidate = $lines[$i++];
            (my $bare = $candidate) =~ s/^\t+// if $dash;
            $bare = $candidate unless defined $bare;
            $bare =~ s/[ \t]+$//;
            if ($bare eq $word) {
                push @shell, $candidate if $kind eq 'shell';
                last;
            }
            push @body, $candidate;
        }
        if ($kind eq 'shell') { push @shell, @body; }
        elsif ($kind eq 'interp') { push @interp, @body; }
    }
}

if ($mode eq 'interp') {
    print join("\n", @interp);
    exit 0;
}

my $text = join("\n", @shell);
$text =~ s{((?:--?m|--message|--body|--title|--notes|-b)(?:=|[ \t]+))(?:"(?:[^"\\]|\\.)*"|'[^']*')}{$1""}g;
$text =~ s{(\b(?:echo|printf)(?:[ \t]+-[a-zA-Z]+)*[ \t]+)(?:"(?:[^"\\]|\\.)*"|'[^']*')}{$1""}g;
print $text;
