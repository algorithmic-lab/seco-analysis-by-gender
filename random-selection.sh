#!/bin/bash

# Define the input and output files
input_file="data/sample/rsample-1M-a2AFullHT-output-with-gender-2024-06-07-12-40-01.csv"
output_file="data/sample/rsample-50k-50k.csv"
num_each_gender=50000

# Create interemdiate files to store results
female_file="female_records.csv"
male_file="male_records.csv"

# Extract female records
awk -F ';' '$4 == "F"' $input_file | shuf | head -n $num_each_gender > $female_file

# Extract male records
awk -F ';' '$4 == "M"' $input_file | shuf | head -n $num_each_gender > $male_file

# Open output file for writing
exec 3> $output_file

# Open female and male files for reading
exec 4< $female_file
exec 5< $male_file

# Read and write lines alternately
for ((i=0; i<$num_each_gender; i++)); do
  if read -u 4 female_line && read -u 5 male_line; then
    echo "$female_line" >&3
    echo "$male_line" >&3
  fi
done

# Close file descriptors
exec 3>&-
exec 4<&-
exec 5<&-

# Clean up intermediate files
rm $female_file $male_file

echo "Created $output_file with $num_each_gender female and $num_each_gender male records."