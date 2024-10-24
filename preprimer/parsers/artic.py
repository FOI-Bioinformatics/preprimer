
def parse_artic(primer_file, prefix):
    """
    MN908947.3	47	78	SARS-CoV-2_400_1_LEFT_1	1	+	CTCTTGTAGATCTGTTCTCTAAACGAACTTT														
    MN908947.3	419	447	SARS-CoV-2_400_1_RIGHT_1	1	-	AAAACGCCTTTTTCAACTTCTACTAAGC												
    MN908947.3	344	366	SARS-CoV-2_400_2_LEFT_0	2	+	TCGTACGTGGCTTTGGAGACTC														
    MN908947.3	707	732	SARS-CoV-2_400_2_RIGHT_0	2	-	TCTTCATAAGGATCAGTGCCAAGCT														
    """
    amplicon_info = {}
    try: 
        with open(primer_file, 'r') as file:
            for line in file:
                # Split the line by tabs or spaces
                parts = line.strip().split()
                # Extract information from parts
                reference_id = parts[0]
                start = int(parts[1])
                stop = int(parts[2])
                artic_primer_name = parts[3]
                pool = int(parts[4])
                strand = parts[5]
                seq = parts[6]
                
                # Extract amplicon number from the primer name
                amplicon_nr = artic_primer_name.split('_')[2]
                
                # Determine direction and artic_primer_name
                if artic_primer_name.endswith('LEFT_1') or artic_primer_name.endswith('LEFT_0'):
                    direction = 'forward'
                    amplicon_name = artic_primer_name.split("_LEFT")[0]
                elif artic_primer_name.endswith('RIGHT_1') or artic_primer_name.endswith('RIGHT_0'):
                    direction = 'reverse'
                    amplicon_name = artic_primer_name.split("_RIGHT")[0]

                
                # Add the information to the dictionary
                if amplicon_name not in amplicon_info:
                    amplicon_info[amplicon_name] = []
                
                amplicon_info[amplicon_name].append({
                    'primer_name': artic_primer_name,
                    'artic_primer_name': artic_primer_name,
                    'strand': strand,
                    'direction': direction,
                    'pool': pool,
                    'start': start,
                    'stop': stop,
                    'seq': seq,
                    'reference_id': reference_id,
                    'amplicon_length': abs(stop-start)
                })
    except:
        print(f"File {primer_file} could not be parsed. Check your input")
        exit()
    return amplicon_info


                    # 'amplicon_length': amplicon_length,
                    # 'primer_name': primer_name,
                    # 'artic_primer_name': artic_primer_name,
                    # 'strand': strand,
                    # 'direction': direction,
                    # 'pool': pool,
                    # 'start': start,
                    # 'stop': stop,
                    # 'seq': seq,
                    # 'size': size,
                    # 'gc_best': gc_best,
                    # 'temp_best': temp_best,
                    # 'mean_gc': mean_gc,
                    # 'mean_temp': mean_temp,
                    # 'score': score,
                    # 'reference_id': "ambigous_consensus"