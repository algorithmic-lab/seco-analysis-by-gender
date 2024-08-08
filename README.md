# gendered-se

An analysis of data from software ecosystems.



## Setup requirements

You will need to pip install:
- wikipedia (to use wiki gendersort)
- unidecode (to use wiki gendersort)
- pandas (to parse gz file of all author names)
- dask (to parse very large files in parallel)

## Empirical analysis

### Run time
Running locally on a 2023 32GB Apple M2 Max MacBook Pro yields the following run time for Wiki-Gendersort to simply: take a name & genderize it using the existing database of names. It assumes that the name is provided in a form accepted by the database (first name only).

| Quantity of names | Seconds to genderize |
| ----------------- | -------------------- |
| 1,000			    | 0.0038s 			   |
| 10,000			| 0.0399s              |
| 100,000           | 0.399s 	           |
| 1,000,000         | 3.9 s                |
| 10,000,000        | 38.8 s               |
| 100,000,000		| 396.2s               |


## Data cleaning & processing

We use the data file from `/data/basemaps/gz/a2AFullHT` on World of Code server da0.

A problem is occurred with either one of the following two consecutive lines from the a2AFulltHT file.

```
"img src=x onerror=prompt(0);"img src=x onerror=prompt(0);0;0
a <HamzaWhitehat@users.noreply.github.com>;"img src=x onerror=prompt(0);0;0
```

Removing the first "problem" line still leads to issues. Removing only the second line, on line 63879, with content `a <HamzaWhitehat@users.noreply.github.com>;"img src=x onerror=prompt(0);0;0`, fixes the parser errors. 

The genderizer, `analyze.py`, was applied to all data.

### Sample data

Sample A (representative) data was randomly collected from the a2AFullHT-clean dataset, in size increments of 10e3, 10e4, 10e5, and 10e6, using the following command `shuf -n <size> a2AFullHT-clean`. Sample B (stratified for equal gender representation) data was collected using `random-selection.sh`. In the event of a randomly selected data point returning zero values in the next process, we iterated to add more random data points for a full and filtered set.


### Collection

We ran `server-side-analysis` to determine the following for each author:
- a list of all commits they made
- a list of all files modified in each commit
- a list of all projects they are involved in

We classified files by programming language / filetype according to their file extension, using the [2023 StackOverflow Developer Survey](https://survey.stackoverflow.co/2023/#technology-most-popular-technologies) to guide us on the languages to consider and (for optimality) the order in which to consider them. The full list is given in `extension-mapping.csv`.

### Timing
The run time for an increasing number of authors is as follows.

Number of authors | Time in seconds | Time (H:M:S)
------------------|---------------- | -- 
100               | 233s   			| 0:03:53
1,000			  |	2,045s			| 0:34:05
10,000			  | 26,139s 		| 7:15:39
100,000       | 915,501s      | 254:18:21


