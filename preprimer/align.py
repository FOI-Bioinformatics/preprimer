import os
from preprimer.utils import FileHandler, PrimerWriter, Aligner

def align(args):
    for output_format in args.output_format:
        if output_format == 'me-pcr':
            output_folder = os.path.join(args.output_folder, "alignment/mepcr")
            FileHandler.check_folder_presence(output_folder, args.force)
        if output_format == 'exonerate':
            output_folder = os.path.join(args.output_folder, "alignment/exonerate")
            FileHandler.check_folder_presence(output_folder, args.force)
        
        with open(args.sts_file, 'r') as file:
            for line in file:
                primer_pair = line.split()
                amplicon_name = primer_pair[0]
                fw_seq = primer_pair[1]
                rw_seq = primer_pair[2]
                if output_format == 'exonerate':
                    PrimerWriter.run_exonerate(f'{amplicon_name}_fw', output_folder, fw_seq, args.reference)
                    PrimerWriter.run_exonerate(f'{amplicon_name}_rw', output_folder, rw_seq, args.reference)
        
        if output_format == 'me-pcr':
            file_name = os.path.join(output_folder, f'{args.prefix}.mepcr.aln')
            output_file_path = Aligner.run_me_pcr(args.sts_file, args.reference, False, file_name)
            print(f'The me-pcr results are written to {output_file_path}')