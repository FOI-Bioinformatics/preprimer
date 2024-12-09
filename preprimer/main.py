import argparse
from preprimer.convert import convert
from preprimer.align import align

def main():
    parser = argparse.ArgumentParser(description="Tool for preparing tiled data")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Convert subparser
    convert_parser = subparsers.add_parser("convert", help="Convert between different formats")
    convert_parser.add_argument("--input-format", choices=['varvamp', 'artic'], help="Input format", required=True)    
    convert_parser.add_argument("--primer-info", help="File with primer information")
    convert_parser.add_argument("--output-folder", help="Output folder")
    convert_parser.add_argument("--prefix", help="File prefix for output files")
    convert_parser.add_argument("--output-format", choices=['artic', 'sts', 'fasta'], nargs='+', help="Output format(s) for primers", required=True)
    convert_parser.add_argument("--reference", help="Fasta of new reference genome")
    convert_parser.add_argument("--force", action="store_true", help="Force remove folders without prompting")
    convert_parser.add_argument("--aligner", choices=['exonerate', 'blast'], help="Output format(s) for primers", required=False, default='blast')

    # Align subparser
    align_parser = subparsers.add_parser("align", help="Align primers to a reference")
    align_parser.add_argument("--sts-file", help="Sts file", required=True)
    align_parser.add_argument("--output-folder", help="Output folder", required=True)
    align_parser.add_argument("--prefix", help="File prefix for output files", required=True)
    align_parser.add_argument("--output-format", choices=['me-pcr', 'primers'], nargs='+', help="Output format(s)", required=True)
    align_parser.add_argument("--reference", help="Complete genome fasta to use as reference", required=True)
    align_parser.add_argument("--force", action="store_true", help="Force operation without prompting")
    align_parser.add_argument("--aligner", choices=['exonerate', 'blast'], help="Output format(s) for primers", required=False, default='blast')

    args = parser.parse_args()

    if args.command == "convert":
        convert(args)
    elif args.command == "align":
        align(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()