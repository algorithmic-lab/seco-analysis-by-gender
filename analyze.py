import logging
from WG.Wiki_Gendersort import wiki_gendersort
import time
import pandas as pd
import multiprocessing
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# should be labeled as "UNK", but sometimes WikiGendersort returns null
def is_unknown(gender):
    return gender not in ["INI", "M", "F", "UNI"]

def is_not_gendered(gender):
    return gender not in ["M", "F", "UNI"]

# take chunk of records from WoC data and roughly estimate a first name to genderize
def process_chunk(chunk):
    try:
        logger.info("Processing next chunk...")

        # initialize name-to-gender database (a python dictionary from txt file)
        WG = wiki_gendersort()

        gender_list = []
        first_name_list = []
        validity_list = []
        processed_list_start = []
        processed_list_end = []

        for idx, record in chunk.iterrows():
            try:
                processed_list_start.append("y")
                gender = "NONE"
                input_string = str(record["userid2"]) 	# second column
                backup_string = str(record["userid1"]) 	# first column

                # ---------- obtain first name and genderize --------------------
                words = input_string.strip().split()

                # use first column only if there is nothing in other column.
                used_first_col = False
                tried_pascal = False
                if len(words) <= 0:
                    words = backup_string.strip().split()
                    used_first_col = True

                # as long as there is something there to parse ...
                if len(words) > 0:
                    # take first word as first name
                    first_name = words[0]

                    # try to get gender
                    gender = WG.assign(first_name)

                    # if it is unknown, try handling pascal case
                    if is_not_gendered(gender) and not tried_pascal:
                        upper_indices = [idx for idx in range(len(first_name)) if first_name[idx].isupper()]
                        if len(upper_indices) >= 2:
                            first_name = first_name[:upper_indices[1]]
                            gender = WG.assign(first_name)

                    # if it is unknown, try again but with first column
                    if is_not_gendered(gender) and not used_first_col:
                        words = backup_string.strip().split()
                        if len(words) > 0:
                            first_name = words[0]

                        gender = WG.assign(first_name)

                        # if still unknown, try with pascal again in first column
                        if is_not_gendered(gender):
                            upper_indices = [idx for idx in range(len(first_name)) if first_name[idx].isupper()]
                            if len(upper_indices) >= 2:
                                first_name = first_name[:upper_indices[1]]
                                gender = WG.assign(first_name)

                    # if it is still unknown, we've done all we can.
                    if is_unknown(gender) and gender != "UNK":
                        gender = "EMPTY"  # uncategorizable

                else:
                    first_name = ""  # it's empty
                    gender = "EMPTY"  # uncategorizable

                # ---------- classify cleanliness of name --------------------
                num_fname_letters = len([c for c in first_name if c.isalpha()])
                validity = "ok"  # no issue with quality found
                if len(first_name) <= 0:
                    validity = "blank"  # name is empty
                elif len(first_name) >= 100:
                    validity = "overlong"  # first name is over 100 characters
                elif num_fname_letters <= (0.9 * len(first_name)):
                    validity = "non-letter"  # over 10% of first name is non-letter characters

                first_name_list.append(first_name)
                gender_list.append(gender)
                validity_list.append(validity)
            except Exception as e:
                logger.error(f"Error processing record {idx}: {e}")
                # If there's an error, we append placeholders to keep lists in sync
                first_name_list.append("")
                gender_list.append("NONE")
                validity_list.append("error")
            finally:
                processed_list_end.append("y")

            if is_unknown(gender) and gender != "UNK":
                logger.warning(f"Weird case labeled as: {gender}, {first_name}")
                logger.warning(f"-- full: {record}")
                logger.warning(f"-- words: {words}")

        # Ensure all lists are of the same length as the chunk
        if len(first_name_list) < len(chunk):
            logger.warning("Some records were not processed correctly.")
            missing_count = len(chunk) - len(first_name_list)
            first_name_list.extend([""] * missing_count)
            gender_list.extend(["NONE"] * missing_count)
            validity_list.extend(["error"] * missing_count)
            processed_list_start.extend([""] * missing_count)
            processed_list_end.extend([""] * missing_count)

        chunk["gender"] = gender_list
        chunk["fname"] = first_name_list
        chunk["validity"] = validity_list
        chunk["processed_start"] = processed_list_start
        chunk["processed_end"] = processed_list_end

        return chunk
    except Exception as e:
        logger.error(f"Error processing chunk: {e}")
        return chunk  # Return the original chunk even in case of error


def print_gender_totals(df):
    gender_totals = {}
    # gender: from wiki gender-sort
    gender_totals["M"] = (df.gender.values == "M").sum()
    gender_totals["F"] = (df.gender.values == "F").sum()
    gender_totals["UNI"] = (df.gender.values == "UNI").sum()
    gender_totals["INI"] = (df.gender.values == "INI").sum()
    gender_totals["UNK"] = (df.gender.values == "UNK").sum()

    # gender: error checking from ours - values should be 0
    gender_totals["EMPTY"] = (df.gender.values == "EMPTY").sum()
    gender_totals["NONE"] = (df.gender.values == "NONE").sum()

    logger.info(gender_totals)

def print_validity_totals(df):
    validity_totals = {}
    validity_totals["ok"] = (df.validity.values == "ok").sum()
    validity_totals["blank"] = (df.validity.values == "blank").sum()
    validity_totals["overlong"] = (df.validity.values == "overlong").sum()
    validity_totals["non-letter"] = (df.validity.values == "non-letter").sum()

    logger.info(validity_totals)

if __name__ == "__main__":
    start_time = time.time()
    current_datetime = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

    # read in chunks of full gz-compressed text file of all author names
    chunksize = 10**6
    colnames = ["userid1", "userid2", "num1", "num2"]

    # i removed this from line 63879 from full dataset (same as above), which didn't cause issue
    input_file = "data/a2AFullHT"
    chunks = pd.read_csv(input_file, sep=';', encoding="ISO-8859-1", names=colnames, chunksize=chunksize, on_bad_lines='warn')

    # Track the number of chunks processed
    num_chunks = 0

    # apply genderizer to each chunk in parallel
    pool = multiprocessing.Pool()
    processed_chunks = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i} with {len(chunk)} records")
        processed_chunk = pool.apply_async(process_chunk, (chunk,))
        processed_chunks.append(processed_chunk)

    pool.close()
    pool.join()

    result = [chunk.get() for chunk in processed_chunks]
    result_df = pd.concat(result, ignore_index=True)


    logger.info("Completed categorizing all names")

    # ----- tally up values we classified -------------
    print_gender_totals(result_df)
    print_validity_totals(result_df)

    uncleaned_output_file = input_file + "-uncleaned-output-with-gender-" + current_datetime + ".csv"
    header = ["userid1", "userid2", "fname", "gender", "validity", "processed_start", "processed_end"]
    result_df.to_csv(uncleaned_output_file, columns=header, sep=";", index=False, encoding="ISO-8859-1")

    # remove duplicates
    original_count = len(result_df.index)
    logger.info(f"Processed {original_count} records.")
    result_df = result_df.drop_duplicates(subset=['userid2'], keep='first', inplace=False)
    deduplicated_count = len(result_df.index)
    duplicates = original_count - deduplicated_count
    logger.info(f"Removed {duplicates} duplicates, for a total of {deduplicated_count} unique developers.")

    deduplicated_output_file = input_file + "-deduplicated-output-with-gender-" + current_datetime + ".csv"
    header = ["userid1", "userid2", "fname", "gender", "validity"]
    result_df.to_csv(deduplicated_output_file, columns=header, sep=";", index=False, encoding="ISO-8859-1")

    # ----- tally up values we classified -------------
    print_gender_totals(result_df)
    print_validity_totals(result_df)

    # ----- Remove invalid data -------------
    logger.info("Removing blank frames ... ")
    blank_mask = result_df.validity.values == "blank"
    result_df = result_df[~blank_mask]
    print_gender_totals(result_df)

    logger.info("Removing overlong frames ... ")
    overlong_mask = result_df.validity.values == "overlong"
    result_df = result_df[~overlong_mask]
    print_gender_totals(result_df)

    logger.info("Removing non-letter frames ... ")
    nonletter_mask = result_df.validity.values == "non-letter"
    result_df = result_df[~nonletter_mask]
    print_gender_totals(result_df)

    # ----- construct unique output file -------------
    logger.info("Writing to output file...")

    output_file = input_file + "-output-with-gender-" + current_datetime + ".csv"
    header = ["userid1", "userid2", "fname", "gender"]
    result_df.to_csv(output_file, columns=header, sep=";", index=False, encoding="ISO-8859-1")
    logger.info("Completed writing to output file...")

    unknown_output_file = input_file + "-output-with-unknown-gender-" + current_datetime + ".csv"
    header = ["userid1", "userid2", "fname", "gender"]
    unknown_mask = result_df.gender.values == "UNK"
    unknowns_df = result_df[unknown_mask]
    unknowns_df.to_csv(unknown_output_file, columns=header, sep=";", index=False, encoding="ISO-8859-1")
    logger.info("Completed writing to output file...")

    unlabeled_output_file = input_file + "-output-with-unlabeled-gender-" + current_datetime + ".csv"
    header = ["userid1", "userid2", "fname", "gender"]
    null_mask = result_df.isnull().any(axis=1)
    null_rows = result_df[null_mask]
    null_rows.to_csv(unlabeled_output_file, columns=header, sep=";", index=False, encoding="ISO-8859-1")

    zero_output_file = input_file + "-output-with-zero-gender-" + current_datetime + ".csv"
    header = ["userid1", "userid2", "fname", "gender"]
    zero_mask = result_df.gender.values == "0"
    zero_df = result_df[zero_mask]
    zero_df.to_csv(zero_output_file, columns=header, sep=";", index=False, encoding="ISO-8859-1")

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Execution time was {elapsed_time} seconds")
