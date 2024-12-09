import os
import shutil
import re
import tempfile
import subprocess
from pathlib import Path
from preprimer.utils import Aligner

def write_sts(file_path, amplicons, reference):
        with open(file_path, 'w') as output_file:
            for key in amplicons:
                amplicon_name = key
                seq_fw = ''
                seq_rw = ''
                amplicon_len = ''
                for primer in amplicons[amplicon_name]:
                    if primer['direction'] == 'forward':
                        seq_fw = primer['seq']
                    if primer['direction'] == 'reverse':
                        seq_rw = primer['seq']
                    amplicon_len = primer['amplicon_length']
                output_file.write(f"{amplicon_name}\t{seq_fw}\t{seq_rw}\t{amplicon_len}\n")

# Write sts output format.
def write_sts_2(file_path, amplicon_info, reference, aligner, force):
    #sts.file
    """
    amplicon_0      actgctgtaggcgtcaaagatt  cggaaataatacggtgggcgaga 2737
    amplicon_1      tcctcatgcgaattcactccca  cgaacagaatgcccacaacaca  2914
    amplicon_2      aattggtaggggcggtygtga   tggactgcgcaaatccaacatc  2571
    amplicon_3      atgccaccgggaaactgtaca   gctgctttgtatgtgcgctttg  2884
    """

    with open(file_path, 'w') as output_file:
        # output_file.write("ID\tSNP-pos\tSNP-state\tForward\tReverse\n")
        for key in amplicon_info:
        # for i, (fw, rw) in enumerate(pairs):
            amplicon_name = key
            seq_fw = ''
            seq_rw = ''
            len = ''
            for primer in amplicon_info[amplicon_name]:
                primer_name = primer['primer_name']
                amplicon_len = primer['amplicon_length']
                seq = primer['seq']
                if primer['direction'] == 'forward':
                    seq_fw = seq
                if primer['direction'] == 'reverse':
                    seq_rw = seq
                amplicon_len = primer['amplicon_length']

                if Aligner.contains_non_atgc(seq):
                    if aligner == 'exonerate':
                        aln_path = Aligner.run_exonerate(primer_name, os.path.dirname(file_path), seq, reference)                   
                    elif aligner == 'blast':
                        aln_path = Aligner.run_blast(primer_name, os.path.dirname(file_path), seq, reference, "0")
                    with open(aln_path, 'r') as file:
                        for line in file:
                            print(line, end='')
                        print(f"WARNING! You are creating an sts with a primer with non ATCG characters")
                        print(f'WARNING! Ambigous bases do not work in me-pcr.')
                        print(f'WARNING! Consider changing the primer of amplicon: {amplicon_name}, primer: {primer_name}, sequence: {seq} to atgc characters {Aligner.contains_non_atgc(seq)}')
                        print(f'WARNING! before using the sts')
                        print(f'WARNING! Alignment in {aln_path}.')
                        if not force:
                            response = input(f"Do you want to continue with ambigous bases in the primers? (y/n): ").strip().lower()
                            if response == 'n':
                                print("Aborted. Change the input primers and try again!")
                                sys.exit(1)
                            else: 
                                pass
                        else: 
                            pass

            output_file.write(f"{amplicon_name}\t{seq_fw}\t{seq_rw}\t{amplicon_len}\n")

def write_fasta(file_path, amplicon_dict):
    with open(file_path, 'w') as output_file:
        for key in amplicon_dict:
            for primer in amplicon_dict[key]:
                output_file.write(f">{primer['artic_primer_name']}\n{primer['seq']}\n")

def write_artic(file_path, amplicon_dict):
    with open(file_path, 'w') as output_file:
        for amplicon_name in amplicon_dict:
            for primer in amplicon_dict[amplicon_name]:
                output_file.write(f"{primer['reference_id']}\t{primer['start']}\t{primer['stop']}\t{primer['artic_primer_name']}\t{primer['pool']}\t{primer['strand']}\t{primer['seq']}\n")
