# PrePrimeR
Prepare primers from different formats, i.e. schemes for tiled sequencing from varvamp to artic format. The script also aligns primers with exonerate and generates amplicons with mepcr.



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
This part coverts the input format into one or multiple other formats

Currently it supports 
input primer formats: 
- varvamp primers.tsv
- artic *.scheme.bed

varVAMP tiled primer schemes generated with https://github.com/jonas-fuchs/varVAMP 

Output formats
- artic (outputs *.scheme.bed and reference.fasta)
- sts (used for insilico pcr with me-pcr)
- fasta (all primer sequences in a multifasta).  

**Example keeping ambiguous consensus from varvamp as reference.**  

This is the default when `--reference` is NOT given as argument.
```bash
preprimer convert --input-format varvamp --primer-info tests/test_data/ASFV_long/primers.tsv --output-folder schemes --output-format artic --prefix ASFV
```


**Example with new sequence as reference and multiple outputs (artic, fasta, sts)**.  

If a reference fasta file is specified with `--reference` the primers will be aligned to this reference and the output will be in relation to the new reference. If a primer gets multiple hits in the new reference it will choose a pair located close to the position of the primer to the old reference. This solutin is chosen since we do not antissipate that the references differs so much. All alignments are saved in folder {output_folder}/alignment/new_reference.  

```
preprimer convert --input-format varvamp --primer-info tests/test_data/ASFV_long/primers.tsv --output-folder schemes --output-format artic fasta sts --prefix ASFV --reference tests/test_data/LR722600.1.fasta
```



If `--force` no prompts will be displayed and
- existing folders will be automatically removed with new
- Amplicons where one or both primers fails to align will be excluded

**Run artic**
How to run artic minion command using the artic scheme converted from varvamp, with the name **prefix** of the scheme and the **directory** from the PrePrimeR output in the command.

```
artic minion ASFV guppy_minion_data/ASFV --scheme-directory schemes/artic/ --read-file guppy_data/sample1.fastq --medaka --medaka-model r941_min_high_g360
```

**Convert artic to sts and fasta**
artic formats can only be converted into fasta and sts, not varvamp. An sts is needed for the Alignment in next section.
```
preprimer convert --input-format artic --primer-info tests/test_data/artic/ASFV/V1/ASFV.scheme.bed --output-format sts fasta  --output-folder schemes --prefix ASFV
```


### Align
Use align to check both the alignment of the primers (exonerate) and the amplicons they produce (mepcr) to a fasta reference of your choice. 

Input:
- sts (can be genereated with convert command)
  
Output:
- me-pcr
- exonerate

The output will be saved in {output_folder}/alignment/mepcr and {output_folder}/alignment/exonerate. The varVAMP primers might contain ambiguous nucleotide characters (not only ATCG) that will be a problem for the me-pcr aligner.  Then, first genereate
```
preprimer align --sts-file tests/test_data/ASFV.sts.tsv --output-format me-pcr exonerate --reference tests/test_data/LR722600.1.fasta --prefix ASFV --output-folder output_alignment --force
```

## Contributing
We welcome contributions to PrePrimeR! If you have suggestions or contributions, please open an issue or pull request.

## License
PrePrimeR is licensed under the MIT License.
