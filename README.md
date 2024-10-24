# PrePrimeR
Prepare primers from different formats, i.e. schemes for tiled sequencing from varvamp to artic format. The script also aligns primers with mepcr or exonerate.

Currently it supports 
input primer formats: 
- varvamp
  
Output formats
- artic (outputs scheme and reference)
- sts (used for insilico pcr with me-pcr)
- fasta (all primer sequence in a multifasta)

## Installation
```
#Create a new environment and install dependencies. Make sure to activate the environment.
conda create -n PrePrimeR exonerate me-pcr
conda activate PrePrimeR

git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip install .
```

## Usage
```shell
preprimer -h
```

### Convert
varVAMP tiled primer schemes generated with https://github.com/jonas-fuchs/varVAMP 

Example keeping the ambiguous consensus sequence from varvamp as reference. 
This is the default when `--reference` is NOT given as argument.
```bash
preprimer convert --input-format varvamp --primer-info varvamp/varvamp_outputfolder/primers.tsv --output-format artic  --prefix SINV
```

Example using a **new sequence** as reference and **multiple outputs**. 
Give the fasta as argument `--reference`.
```bash
preprimer convert --input-format varvamp --primer-info varvamp/varvamp_outputfolder/primers.tsv --output-format artic fasta sts  --output-folder schemes --prefix SINV --reference NC_123456.fasta
```

This text will be promted
```console
Do you want to remove the existing folder and create a new 'test_schemes/artic/SINV/V1'? (y/n): y
Folder 'schemes/artic/asfv/V1' has been removed.  
Output folder schemes/artic/asfv/V1 created successfully!
Output folder schemes/fasta created successfully!
Output folder schemes/sts created successfully!
```
The artic minion command using the scheme could then look like this, with the name **prefix** of the scheme and the **directory** from the PrePrimeR output in the command.

```
artic minion SINV guppy_minion_data/SINV --scheme-directory schemes/artic/ --read-file guppy_data/sample1.fastq --medaka --medaka-model r941_min_high_g360
```
The varVAMP primers might contain ambiguous nucleotide characters (not only ATCG) that will be a problem for the aligner in PrePrimeR to find the correct location of the primer in the new reference. This software will look for these characters during alignment and promt if they are found. 

If `--force` no prompts will be displayed and
- existing folders will be automatically removed with new
- Amplicons where one or both primers fails to align will be excluded


### Align

```
preprimer align --input-format varvamp --primer-info varvamp/varvamp_outputfolder/primers.tsv --output-format --output-folder schemes --prefix SINV --reference NC_123456.fasta
```

## Contributing
We welcome contributions to PrePrimeR! If you have suggestions or contributions, please open an issue or pull request.

## License
PrePrimeR is licensed under the MIT License.
