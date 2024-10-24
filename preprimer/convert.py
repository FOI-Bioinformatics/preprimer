import os
from preprimer.parsers.varvamp import parse_varvamp
from preprimer.parsers.artic import parse_artic
from preprimer.utils import FileHandler, AmpliconUpdater
from . import writers

def convert(args):
    amplicon_info = {}
    reference = ""
    primer_info_dir = os.path.dirname(args.primer_info)

    # Read varvamp primer file into dictionary
    if args.input_format == 'varvamp':
        print("\n#######################################")
        print("## PARSING VARVAMP ")
        print("#######################################\n")
        print(f"Reading varvamp primer information from {args.primer_info} into a dictionary\n")
        if args.reference is None:
            reference = args.reference if args.reference else os.path.join(primer_info_dir, "ambiguous_consensus.fasta")
        else: 
            reference = args.reference
        amplicon_info = parse_varvamp(args.primer_info, args.prefix)

    # Read artic primer file into dictionary
    elif args.input_format == 'artic':
        print("\n #######################################")
        print("## PARSING ARTIC ")
        print("#######################################\n")
        # artic_dir = os.path.dirname(args.primer_info)
        old_file_prefix, ext = os.path.splitext(os.path.basename(args.primer_info))
        amplicon_info = parse_artic(args.primer_info, args.prefix)
        #No new reference is specified. Use the existing artic reference
        if args.reference is None:
            reference = os.path.join(primer_info_dir, old_file_prefix + "reference.fasta")
        else: 
            reference = args.reference
    #Update the dictionary with the new reference
    if args.reference:        
        print("\n#######################################")
        print("## UPDATING PRIMERS TO NEW REFERENCE ##")
        print("#######################################\n")
        print("A new reference is given. Exonerate will be used to find new primer positions.\n")
        new_reference_alignment_dir = os.path.join(args.output_folder, "alignment/new_reference")
        print(f"Saving alignments to: {new_reference_alignment_dir}\n")
        #Returns true if a new folder is created
        if not FileHandler.check_folder_exists(new_reference_alignment_dir, args.force):
            exit()
        updated_amplicon_info = AmpliconUpdater.translate_amplicon_info_to_new_reference(amplicon_info, reference, new_reference_alignment_dir, args.force)
        amplicon_info = updated_amplicon_info

    ## Output the dictionary in the specified formats
    for output_format in args.output_format:
        if output_format == 'artic':
            print("\n######################################")
            print("## PRINTING ARTIC ")
            print("#######################################\n")
            artic_scheme_filepath = os.path.join(args.output_folder, f"artic/{args.prefix}/V1/{args.prefix}.scheme.bed")
            artic_reference_filepath = os.path.join(args.output_folder, f"artic/{args.prefix}/V1/{args.prefix}.reference.fasta")
            artic_folder = os.path.dirname(artic_scheme_filepath)
            print(f"Reference and primer bedfile for use with \"artic minion\" is prepared in the specified folder")
            print(f"reference: {artic_scheme_filepath}")
            print(f"scheme bed: {artic_reference_filepath}\n")
            print("Primers will be named {prefix}_{amplicon_nr}_RIGHT_0 and {prefix}_{amplicon_nr}_LEFT_0\n")
            if FileHandler.check_folder_exists(artic_folder, args.force):
               writers.write_artic(artic_scheme_filepath, amplicon_info)
            else: 
                "No artic files will be printed"
            FileHandler.copy_file(reference, artic_reference_filepath)
        elif output_format == 'fasta':
            print("\n#######################################")
            print("## PRINTING FASTA ")
            print("#######################################\n")
            primer_fasta_filepath = os.path.join(args.output_folder, f"fasta/{args.prefix}.fasta")
            print(f"Fasta file with all primers are printed in the specified output folder:")
            print(f"fasta: {primer_fasta_filepath}\n")
            print("Primers will be named {prefix}_{amplicon_nr}_RIGHT_0 and {prefix}_{amplicon_nr}_LEFT_0\n")
            
            if FileHandler.check_folder_exists(os.path.dirname(primer_fasta_filepath), args.force):
                writers.write_fasta(primer_fasta_filepath, amplicon_info)
            else: 
                "No fasta will be printed"
        elif output_format == 'sts':
            print("\n#######################################")
            print("## PRINTING STS ")
            print("#######################################\n")
            sts_filepath = os.path.join(args.output_folder, f"sts/{args.prefix}.sts.tsv")
            print(f"sts-file used in me-pcr will be saved in the specified output folder:")
            print(f"sts: {sts_filepath}")
            print("Primers will be named {prefix}_{amplicon_nr}_RIGHT_0 and {prefix}_{amplicon_nr}_LEFT_0\n")
            if FileHandler.check_folder_exists(os.path.dirname(sts_filepath), args.force):
                writers.write_sts(sts_filepath, amplicon_info, reference)
            else: 
                "No sts will be printed"