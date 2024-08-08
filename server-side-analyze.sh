#!/usr/bin/env bash

# File is designed to be run on the WOC da0 server
# Expected usage: time (ssh da0 server-side-analyze.sh <filename> | cat > output-file)


# input file validation
if [ ! -f "$1" ];
then
  echo "ERROR: Input file does not exist."
  exit 1
fi


# default start record is 1
start_record=${2:-1}
current_record=0
num_authors=0

# create a list of types of files, based on extension
# for consistency, this list is used to populate the output file
# all file types considered are provided in csv file
declare -A ftypes_extensions
declare -A ftypes_filenames
declare -a language_order

skip_first_line=true
while IFS=, read -r key extension_regex filename_regex note; do

  if $skip_first_line; then
    skip_first_line=false
    continue
  fi

  # skip empty lines
  if [ -z "$key" ]; then
    continue
  fi

  # store key order -- check against languages IN THIS ORDER
  language_order+=("$key")

  # use first column as key in associative array
  # value is the regular extension matching that type of file
  ftypes_extensions["$key"]="$extension_regex"
  
  # if there is one, value is the regular expression matching the filename
  if [ -z "$filename_regex" ]; then
    ftypes_filenames["$key"]="$filename_regex"
  fi

done < "extension-mapping.csv"

# also count everything that doesnt fall into a given category
ftypes_extensions["Uncategorized"]=""

# and output their names to a text file
#declare -A unknown_extensions
#uncat_names_ofile="uncategorized-all-filenames-output.txt"
#uncat_exts_ofile="uncategorized-extensions-output.txt"
#echo "" > "${uncat_exts_ofile}"
#echo "" > "${uncat_names_ofile}"


# construct header of semi-colon separated file if starting from the 1st record
if [ "$start_record" -eq 1 ]; then
  echo "sep=;"
  echo -n "UserID1;UserID2;FName;Gender;Commits;Projects;TotalFiles;"
  for language in "${language_order[@]}"; do
    echo -n "$language;"
  done
  echo "Uncategorized"
fi


skip_first_line=true

# for each author in list of files - assumes we already obtained gender in column 5
while IFS=\; read -r userid1 userid2 fname gender; do

  # skip first line of header data from input csv file
  if $skip_first_line; then
    skip_first_line=false
    continue
  fi

  current_record=$((current_record + 1))
  num_authors=$((num_authors+1))

  # skip records until the start_record is reached
  if [ "$current_record" -lt "$start_record" ]; then
    >&2 echo "Skipped: ${current_record}"
    continue
  fi

  # count each commit (semicolon separated) by this author; omit first entry which is author name
  num_commits=$(echo "${userid2}" | ~/lookup/getValues a2c | cut -d ';' -f 2- | tr ';' '\n' | wc -l)
  #num_commits=0 #TODO uncomment (speed run)

  # count each project by this author
  num_projects=$(echo "${userid2}" | ~/lookup/getValues a2p | cut -d ';' -f 2- | tr ';' '\n' | wc -l)
  #num_projects=0 #TODO uncomment (speed run)

  # get a list of all files this author edited
  files=$(echo "${userid2}" | ~/lookup/getValues a2f | cut -d ';' -f 2-)
  num_total_files=$(echo "$files" | tr ';' '\n' | wc -l)


  # for this author, setup initially 0 count dictionary
  declare -A authors_ftypes
  for language in "${language_order[@]}" # TODO: USE DICT
  do
    authors_ftypes["$language"]=0
  done
  authors_ftypes["Uncategorized"]=0


  # go through each file to classify its language based on extension
  for file in $(echo ${files} | sed "s/;/ /g")
  do
    file_name="${file##*/}"
    lowercase_file_name=$(echo "$file_name" | tr '[:upper:]' '[:lower:]')
    lowercase_extension="${lowercase_file_name##*.}"


    # match extension to regular expression and increase corresponding language count
    #ISSUE: Prolog and Perl both share .pl as file extensions

    matched=false
    if [ "$matched" = false ]; then
      for language in "${language_order[@]}"; do
        if [[ $lowercase_extension =~ ^(${ftypes_extensions[$language]})$ ]]; then
          matched=true
          ((authors_ftypes[$language]++))
          break
        elif [[ -v ftypes_filenames[$language] ]]; then
          if [[ $lowercase_file_name =~ ^(${ftypes_filenames[$language]})$ ]]; then
            matched=true
            ((authors_ftypes[$language]++))
            break
          fi
        fi
      done
    fi


    # if it still did not match any, it is unknown
    if [ "$matched" = false ]; then
      ((authors_ftypes["Uncategorized"]++))

      ## keep track of these types for output
      #if [[ -v unknown_extensions[$lowercase_extension] ]]; then
      #  ((unknown_extensions["$lowercase_extension"]++))
      #else
      #  unknown_extensions["$lowercase_extension"]=1
      #fi

      #echo "$file_name" >> "$uncat_names_ofile"
      #>&2 echo "---unmatched filename: ${file_name}"
      #>&2 echo "Unmatched ext: ${lowercase_extension}"

    fi

  done


  # print uncategorized extensions
  #  echo "sep=;" > "$uncat_exts_ofile" # reset
  #  for uncat_ext in "${!unknown_extensions[@]}"; do
  #    echo "$uncat_ext;${unknown_extensions[$uncat_ext]}" >> "$uncat_exts_ofile"
  #  done

  # print output totals for each author; use original order as given by indexed list
  echo -n "${userid1};${userid2};${fname};${gender};${num_commits};${num_projects};${num_total_files};"
  for language in "${language_order[@]}"; do
    echo -n "${authors_ftypes[$language]};"
  done
  echo -n "${authors_ftypes["Uncategorized"]}"
  echo ""

  # give progress update to stderr
  >&2 echo "Number of authors procesed: ${num_authors}"

done < "$1"





