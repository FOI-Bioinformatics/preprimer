

# Read varvamp tiling primer information into a dictionary
def parse_varvamp(primer_file, prefix):
    # primers.tsv

    # amlicon_name	amplicon_length	primer_name	pool	start	stop	seq	size	gc_best	temp_best	mean_gc	mean_temp	score
    # amplicon_0	2737	FW_0	0	5	26	actgctgtaggcgtcaaagatt	22	45.5	58.3	45.5	58.3	4.7
    # amplicon_0	2737	RW_60	0	2719	2741	cggaaataatacggtgggcgaga	23	52.2	60.8	52.2	60.8	3.0
    # amplicon_1	2914	FW_87	0	4171	4192	tcctcatgcgaattcactccca	22	50.0	59.8	50.0	59.8	0.9
    # amplicon_1	2914	RW_135	0	7063	7084	cgaacagaatgcccacaacaca	22	50.0	60.0	50.0	60.0	0.6
    # amplicon_2	2571	FW_191	0	8692	8712	aattggtaggggcggtygtga	21	52.4	60.0	54.8	60.9	0.7
    # amplicon_2	2571	RW_292	0	11241	11262	tggactgcgcaaatccaacatc	22	50.0	60.1	50.0	60.1	0.7
    # amplicon_3	2884	FW_311	0	12448	12468	atgccaccgggaaactgtaca	21	52.4	60.0	52.4	60.0	0.5
 
    ## Check input


    amplicon_info = {}
    primer_file_path = primer_file
    with open(primer_file_path, 'r') as file:
        # Skip the header line
        next(file)
        for line in file:
            # Split the line by tabs
            parts = line.strip().split('\t')
            # Extract information from parts
            amplicon_name = parts[0]
            amplicon_length = int(parts[1])
            primer_name = parts[2]
            pool = int(parts[3])
            start = int(parts[4])
            stop = int(parts[5])
            seq = parts[6]
            size = int(parts[7])
            gc_best = float(parts[8])
            temp_best = float(parts[9])
            mean_gc = float(parts[10])
            mean_temp = float(parts[11])
            score = float(parts[12])
            amplicon_nr = str(int(amplicon_name.split("_")[1]))
            # Add the information to the dictionary
            if amplicon_name not in amplicon_info:
                amplicon_info[amplicon_name] = []
            if primer_name.startswith('FW'):
                direction = 'forward'
                artic_primer_name = f"{prefix}_{amplicon_nr}_LEFT_0"
                strand = '+'
            if primer_name.startswith('RW'):
                direction = 'reverse'
                artic_primer_name = f"{prefix}_{amplicon_nr}_RIGHT_0"
                strand = '-'
            amplicon_info[amplicon_name].append({
                'amplicon_length': amplicon_length,
                'primer_name': primer_name,
                'artic_primer_name': artic_primer_name,
                'strand': strand,
                'direction': direction,
                'pool': pool,
                'start': start,
                'stop': stop,
                'seq': seq,
                'size': size,
                'gc_best': gc_best,
                'temp_best': temp_best,
                'mean_gc': mean_gc,
                'mean_temp': mean_temp,
                'score': score,
                'reference_id': "ambigous_consensus"
            })
    return amplicon_info