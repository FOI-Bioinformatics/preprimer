import sys
import os
import shutil
import re
import tempfile
import subprocess
from pathlib import Path

##
## Contains three classes:
## - FileHandler
## - AmpliconUpdater
## - Aligners

class FileHandler:
    @staticmethod
    def ask_remove_folder(directory, force=False):
        if not force:
            response = input(f"Do you want to remove the existing folder and create a new '{directory}'? (y/n): ").strip().lower()
            if response == 'y':
                shutil.rmtree(directory)
                print(f"Folder '{directory}' has been removed.")
                return True
            else:
                print("Folder removal canceled.")
                return False
        else:
            shutil.rmtree(directory)
            print(f"Folder '{directory}' has been removed.")
            return True

    @staticmethod
    def check_folder_exists(directory, force=False):
        if not os.path.exists(directory):
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"Output folder {directory} created successfully!")
            return True
        else:
            print(f"Output folder {directory} already exists")
            if FileHandler.ask_remove_folder(directory, force):
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"Output folder {directory} created successfully!")
                return True
            else:
                print("end")
                return False

    @staticmethod
    def copy_file(src, dst):
        shutil.copy(src, dst)

#___________________________________________________________
#___________________________________________________________
class AmpliconUpdater:
    @staticmethod
    def find_closest_pair(fw_primer_list, rw_primer_list, old_amplicon_length):
        forward = None
        reverse = None
        min_difference = float('inf')
        length = None
        for fw_dict in fw_primer_list:
            for rw_dict in rw_primer_list:
                start = min(fw_dict['start'], rw_dict['stop'])
                end = max(fw_dict['start'], rw_dict['stop'])
                current_length = end - start

                difference = abs(current_length - old_amplicon_length)

                if difference < min_difference:
                    min_difference = difference
                    length = current_length
                    forward = fw_dict
                    reverse = rw_dict

        return forward, reverse, length

    @staticmethod
    def translate_amplicon_info_to_new_reference(amplicon_info, reference_fasta, output_dir, aligner, force=False, ):
        updated_amplicon_info = {}
        for amplicon_name, primers in amplicon_info.items():
            old_forward_primer, old_reverse_primer = primers
            old_length = old_forward_primer['amplicon_length']
            alignments = []
            exclude_amplicon = []

            for primer in primers:
                primer_name = primer['primer_name']
                primer_seq = primer['seq']
                parsed_alignment = ""
                if aligner == 'exonerate':
                    alignment_output = Aligner.run_exonerate(primer_name, output_dir, primer_seq, reference_fasta, "6")
                    parsed_alignment = Aligner.parse_exonerate_output(alignment_output)
                elif aligner == 'blast':
                    alignment_output = Aligner.run_blast(primer_name, output_dir, primer_seq, reference_fasta, "6")
                    parsed_alignment = Aligner.parse_blast_output(alignment_output)
                # If parsing exonerate output fails i.e. no alignments found
                if not parsed_alignment:
                    print(f"\nNo alignment found for primer {primer_name} in amplicon {amplicon_name} to {reference_fasta}.")
                    if not force:
                        user_input = input(f"Do you want to continue anyway?  (y/n): ")
                        if user_input.lower() == 'n':
                            print(f"Program will exit. Try a different reference")
                            exit()
                    else: 
                        print("Option --force excludes by default.")
                    print(f"Amplicon named \"{amplicon_name}\" excluded.\n")
                elif parsed_alignment:
                    alignments.append(parsed_alignment)

            #A succefull alignment where both primers have have one ore more hits
            if len(alignments) == 2:
                forward_parsed, reverse_parsed = alignments
                if forward_parsed and reverse_parsed:
                    forward_primer, reverse_primer, amplicon_length = AmpliconUpdater.find_closest_pair(forward_parsed, reverse_parsed, old_length)
                    updated_primers = []
                    for old_primer, new_primer in zip(primers, [forward_primer, reverse_primer]):
                        updated_primer = old_primer.copy()
                        for key in old_primer.keys():
                            if key in new_primer:
                                updated_primer[key] = new_primer[key]
                        updated_primer['strand'] = '+' if updated_primer['start'] < updated_primer['stop'] else '-'
                        updated_primer['amplicon_length'] = amplicon_length
                        updated_primers.append(updated_primer)
                    
                    if updated_primers:
                        updated_amplicon_info[amplicon_name] = updated_primers
            elif len(alignments) == 0:
                continue

        return updated_amplicon_info

#___________________________________________________________
#___________________________________________________________
class Aligner:
    @staticmethod
    def run_me_pcr(primer_sts_file, reference_genome,  use_temp_file, regular_filepath):
        if use_temp_file:
            # Create a temporary file in the specified folder
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as output_file:
                output_file_path = output_file.name
        else:
            # Create a regular file in the specified folder
            if regular_filepath is None:
                raise ValueError("A regular filename must be provided if not using a temporary file.")
            output_file_path = regular_filepath

        # Define me-PCR command
        me_pcr_command = f"me-PCR {primer_sts_file} {reference_genome} O={output_file_path} M=1000"
        # Run me-PCR command
        subprocess.run(me_pcr_command, shell=True)

        return output_file_path

    @staticmethod
    def run_exonerate(id, output_path, sequence, reference_genome):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as seq_file:
            seq_file.write(f">{id}\n" + sequence)
            seq_file_path = seq_file.name
       
        exonerate_command = [
            "exonerate",
            "--model", "affine:local",
            "--query", seq_file_path,
            "--target", reference_genome,
            "--showalignment", "TRUE",
            "--showvulgar", "FALSE",
            "--showcigar", "TRUE",
            "--ryo", "%qas",
            "--percent", "90",
            "--bestn", "1"
        ]
        output_file_path = f"{output_path}/{id}.aln"
        with open(output_file_path, 'w') as output_file:
            subprocess.run(exonerate_command, stdout=output_file, text=True)
        return output_file_path

    @staticmethod
    def parse_exonerate_output(output_file_path):
        alignments = []
        alignment = {}
        
        with open(output_file_path, 'r') as file:
            lines = file.readlines()
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('cigar:'):
                # Process cigar line and add alignment to the list
                cigar_parts = line.split()
                if len(cigar_parts) >= 8:
                    alignment['primer_name'] = cigar_parts[1]
                    alignment['query_start'] = int(cigar_parts[2])
                    alignment['query_end'] = int(cigar_parts[3])
                    alignment['reference_id'] = cigar_parts[5]
                    alignment['start'] = int(cigar_parts[6])
                    alignment['stop'] = int(cigar_parts[7])
                    alignment['strand'] = cigar_parts[8]
                    alignment['score'] = float(cigar_parts[9])
                    alignment['cigar'] = f'{cigar_parts[10]}{cigar_parts[11]}'
                    
                    # Add alignment to list if all fields are present
                    if all(key in alignment for key in ['query_start', 'query_end', 'start', 'stop', 'score']):
                        alignments.append(alignment)
                        alignment = {}
        return alignments
    
    @staticmethod
    def run_blast(id, output_path, sequence, reference_genome, format):
        # Ensure absolute paths
        reference_genome = os.path.abspath(reference_genome)
        output_path = os.path.abspath(output_path)
        
        # Create a temporary FASTA file for the query sequence
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as seq_file:
            print("Analysing: "+ id)
            seq_file.write(f">{id}\n{sequence}")
            seq_file_path = seq_file.name
        
        # Ensure the reference genome is formatted as a BLAST database
        blast_db_prefix = os.path.splitext(os.path.basename(reference_genome))[0]
        blastdb_output = output_path +"/db/"+f"{blast_db_prefix}"
        if not os.path.exists(blastdb_output+".nhr"):
            if not os.path.exists(reference_genome):
                raise FileNotFoundError(f"Reference genome file not found: {reference_genome}")
            try:
                blastdb_command = ["makeblastdb", "-in", reference_genome, "-dbtype", "nucl", "-out", blastdb_output]
                # print(' '.join(blastdb_command))
                subprocess.run(blastdb_command, check=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to create BLAST database: {e}")

        # Define the BLAST output file
        output_file_path = os.path.join(output_path, f"{id}.blast")
        # Run BLAST
        blast_command = [
            "blastn",
            "-query", seq_file_path,
            "-db", blastdb_output,
            "-out", output_file_path,
            "-outfmt", format,  # Tabular format
            "-evalue",  "1e-4",
            "-task", "blastn-short"
        ]
        try:
            subprocess.run(blast_command, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"BLAST alignment failed: {e}")
        finally:
            os.remove(seq_file_path)

        return output_file_path
    
    @staticmethod
    def parse_blast_output(output_file_path):
        alignments = []
        
        # Define column indices based on BLAST's tabular output
        column_indices = {
            'query_id': 0,
            'subject_id': 1,
            'percent_identity': 2,
            'alignment_length': 3,
            'mismatches': 4,
            'gap_opens': 5,
            'query_start': 6,
            'query_end': 7,
            'subject_start': 8,
            'subject_end': 9,
            'evalue': 10,
            'bit_score': 11
        }
        
        with open(output_file_path, 'r') as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) >= 12:
                    alignment = {
                        'primer_name': parts[column_indices['query_id']],
                        'reference_id': parts[column_indices['subject_id']],
                        'query_start': int(parts[column_indices['query_start']]),
                        'query_end': int(parts[column_indices['query_end']]),
                        'start': int(parts[column_indices['subject_start']]),
                        'stop': int(parts[column_indices['subject_end']]),
                        'percent_identity': float(parts[column_indices['percent_identity']]),
                        'alignment_length': int(parts[column_indices['alignment_length']]),
                        'score': float(parts[column_indices['bit_score']]),
                        'evalue': float(parts[column_indices['evalue']])
                    }
                    alignments.append(alignment)
        
        return alignments

    @staticmethod
    def contains_non_atgc(string):
        # Define a regular expression pattern to match any character except 'a', 't', 'c', and 'g'
        pattern = re.compile(r'[^atcg]', re.IGNORECASE)
        # Search for any non-ATCG characters in the string
        non_atgc_chars = pattern.findall(string)
        # If a match is found, return True (indicating presence of non-ATCG characters), otherwise return False
        return non_atgc_chars