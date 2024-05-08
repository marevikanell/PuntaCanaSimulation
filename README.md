# PuntaCanaSimulation
OS Project 2024, simulating the Paradise Festival in Punta Cana, DR.

# Table of Content 

1. Introduction 
2. Repository Content Description
3. Installation & Usage 
4. Further Improvements 
5. Credits 

# Introduction

Welcome to the Punta Cana Festival Simulation project! This repository contains a Python-based simulation that models the dynamic environment of a large-scale festival. The simulation incorporates multithreading and object-oriented programming to realistically depict various festival activities such as attendee interactions, service operations, and artist performances.

# Repository Content Description

To be able to execute this project, read the following descriptions on the content of the repository. Download the following files and the libraries required by the installation section.
- "punta_cana_festival.py" : python file to run the simulation
- "attendees_seed_0.csv": sql table of attendees used to perfom the analysis for the report
- "orders_seed_0_csv": sql table of orders used to perfom the analysis for the report
- "Punta_Cana_Festival_Simulation_Report.pdf": Academic report for the description of the project
- "example_output.txt": An example of the kernel output, with all the printing statements that visualize the simulation of the festival
- "results_analysis.ipynb": Jubyter Notebook of the analysis conducted using "orders_seed_0.csv" & "attendees_seed_0.csv"
- "sql_queries.mb": A basic guide of the simple queries required to visualize the contents of the tables on the SQL database

# Installation 

To be able to run our program, make sure you have the following things installed:

Python programming language 

Libraries - In order to run our program, we make use of the following 7 libraries: 

- threading
- time
- concurrent.futures
- random
- tracebook
- datetime
- mysql.connector

Now that we have the required libraries set up, open the "punta_cana_festival.py" file and run the program.
- the only point that requires attention is your sql connection, ensure that the correct host, root, and password (if required) are set to establish the connection for your server.

We have developed this project on a **macOS Ventura**

# Usage

Only one file "punta_cana_festival.py" is required to run the simulation successfully.

# Credits 

This project was created for our Operating Systems and Parallel Computing course at IE University. The project was created by: 

- Maria Evrydiki Kanellopoulou
- Jaime Berasategui Cabezas
- José Urgal Saracho

