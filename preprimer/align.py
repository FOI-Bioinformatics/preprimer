import os
from preprimer.utils import FileHandler, Aligner
from . import writers

def align(args):
    for output_format in args.output_format:
        if output_format == 'me-pcr':
            output_folder = os.path.join(args.output_folder, "alignment/mepcr")
            FileHandler.check_folder_exists(output_folder, args.force)
        if output_format == 'primers':
            output_folder = os.path.join(args.output_folder, "alignment/primers")
            FileHandler.check_folder_exists(output_folder, args.force)
            print("\nRunning alignment of primers:")
            with open(args.sts_file, 'r') as file:
                for line in file:
                    primer_pair = line.split()
                    amplicon_name = primer_pair[0]
                    fw_seq = primer_pair[1]
                    rw_seq = primer_pair[2]
                    if args.aligner == 'exonerate':
                        Aligner.run_exonerate(f'{amplicon_name}_fw', output_folder, fw_seq, args.reference)
                        Aligner.run_exonerate(f'{amplicon_name}_rw', output_folder, rw_seq, args.reference)
                    elif args.aligner == 'blast':
                        Aligner.run_blast(f'{amplicon_name}_fw', output_folder, fw_seq, args.reference, "0")
                        Aligner.run_blast(f'{amplicon_name}_rw', output_folder, rw_seq, args.reference, "0")
        
        if output_format == 'me-pcr':
            file_name = os.path.join(output_folder, f'{args.prefix}.mepcr.aln')
            output_file_path = Aligner.run_me_pcr(args.sts_file, args.reference, False, file_name)
            print(f'The me-pcr results are written to {output_file_path}')