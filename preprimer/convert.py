import os
from preprimer.parsers.varvamp import parse_varvamp
from preprimer.parsers.artic import parse_artic
from preprimer.utils import FileHandler, PrimerWriter, AmpliconUpdater

def convert(args):
    amplicon_info = {}
    reference = ""

    if args.input_format == 'varvamp':
        varvamp_dir = os.path.dirname(args.primer_info)
        reference = args.reference if args.reference else os.path.join(varvamp_dir, "ambiguous_consensus.fasta")
        required_files = [reference, args.primer_info]
        FileHandler.search_missing_files(required_files)
        amplicon_info = parse_varvamp(args.primer_info, args.prefix)
        if args.reference:
            print('A new reference is given. Exonerate will be used to find new primer positions.')
            new_reference_alignment_dir = os.path.join(args.output_folder, "alignment/new_reference")
            FileHandler.check_folder_presence(new_reference_alignment_dir, args.force)
            updated_amplicon_info = AmpliconUpdater.translate_amplicon_info_to_new_reference(amplicon_info, reference, new_reference_alignment_dir)
            amplicon_info = updated_amplicon_info
    elif args.input_format == 'artic':
        artic_dir = os.path.dirname(args.primer_info)
        old_file_prefix, ext = os.path.splitext(os.path.basename(args.primer_info))
        if args.reference is None:
            reference = os.path.join(artic_dir, old_file_prefix + "reference.fasta")
        required_files = [reference, args.primer_info]
        FileHandler.search_missing_files(required_files)
        amplicon_info = parse_artic(args.primer_info, args.prefix)
        if args.reference:
            new_reference_alignment_dir = os.path.join(args.output_folder, "alignment/new_reference")
            FileHandler.check_folder_presence(new_reference_alignment_dir, args.force)
            updated_amplicon_info = AmpliconUpdater.translate_amplicon_info_to_new_reference(amplicon_info, reference, new_reference_alignment_dir)
            amplicon_info = updated_amplicon_info

    for output_format in args.output_format:
        if output_format == 'artic':
            artic_scheme_filepath = os.path.join(args.output_folder, f"artic/{args.prefix}/V1/{args.prefix}.scheme.bed")
            artic_reference_filepath = os.path.join(args.output_folder, f"artic/{args.prefix}/V1/{args.prefix}.reference.fasta")
            artic_folder = os.path.dirname(artic_scheme_filepath)
            FileHandler.check_folder_presence(artic_folder, args.force)
            PrimerWriter.write_artic_scheme(artic_scheme_filepath, amplicon_info)
            FileHandler.copy_file(reference, artic_reference_filepath)
        elif output_format == 'fasta':
            primer_fasta_filepath = os.path.join(args.output_folder, f"fasta/{args.prefix}.fasta")
            FileHandler.check_folder_presence(os.path.dirname(primer_fasta_filepath), args.force)
            PrimerWriter.write_fasta(primer_fasta_filepath, amplicon_info)
        elif output_format == 'sts':
            sts_filepath = os.path.join(args.output_folder, f"sts/{args.prefix}.sts.tsv")
            FileHandler.check_folder_presence(os.path.dirname(sts_filepath), args.force)
            PrimerWriter.write_sts(sts_filepath, amplicon_info, args.reference)