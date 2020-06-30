import sys   # Not sure I need this anymore.
import pandas as pd
import numpy as np
import json
import os
import datetime

timestamp = str(datetime.datetime.now())
time_stamp= timestamp.replace(" ","_").replace(":","-").split(".")[0]

# GOOD # Boolean: does the config file exist? https://docs.python.org/2/library/os.path.html
def ConfigBoolean():
    exists = os.path.exists('RefGenConfig.json')
    return exists

config_boo = ConfigBoolean()

# GOOD # Imports json config file
def ImportConfigFile():
    with open('RefGenConfig.json') as f:
        configdata = json.load(f)
        return configdata

# GOOD # Returns list of 13 BL levels
def DefaultHierarchy(configfile):
    if config_boo == True and configfile["Hierarchy"] != "":              # If config file exists, that provides the default hierarchy.
        L = configfile["Hierarchy"]
    else:                                   # Else, the default hierarchy is 13 hard-coded BL levels.
        L = ["Fonds","Sub-fonds","Sub-sub-fonds","Sub-sub-sub-fonds","Series","Sub-series","Sub-sub-series","Sub-sub-sub-series","File","Item","Sub-item","Sub-sub-item","Sub-sub-sub-item"]
    return L

# GOOD # Returns default enccoding.
def SetEncoding(configfile):
    if config_boo == True:                 # If the config file exists, the default encoding will be taken from there.
        return configfile["Encoding"]
    else:                                       # If there is no config file, the default encoding will be utf-8-sig.
        return "utf-8-sig"

def WorksheetName(configfile,worksheetspresent):
    if config_boo == True and configfile["ExcelWorksheet"] in worksheetspresent:
        worksheet = configfile["ExcelWorksheet"]   
    else:
        if len(worksheetspresent) == 1:         # If there is only one sheet, there is no user choice needed.
            worksheet = worksheetspresent[0]
        else:
            print()
            print("Worksheets present in Excel file: ")
            print("-->",worksheetspresent)
            worksheet = input("Enter the name of the Excel worksheet you want to upload (e.g. Sheet1): ")
    return worksheet

# GOOD # Looks at config file and returns directory to find the import file in. If no config file configfile blank, it will default to iporting file from same location as program.
def ImportFilePath(directory,prefix,configfile):
    if config_boo == True and configfile["ImportFilepath"] == "":
        return("")
    elif config_boo == False:
        return("")
    elif config_boo == True and configfile["ImportFilepath"] != "" and configfile["ImportPathUsePrefix"].upper() == "YES":
        NameStart = prefix+" "
        folder_list = [ item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item)) ]      # returns list of folders in specified directory
        for thing in folder_list:
            if NameStart in thing or prefix == thing:
                a = directory+"/"+thing+"/"           # Returns name of the folder to enter, based on the EAP ref (prefix)
                break
            else:
                a = "ERROR: The folder directory is incorrect."
        if a == "ERROR: The folder directory is incorrect.":
            print(a)
            sys.exit()
        return a
    elif config_boo == True and configfile["ImportFilepath"] != "" and configfile["ImportPathUsePrefix"].upper() == "NO":
        return directory+"/"
    
# Imports csv or Excel file and converts to pandas dataframe
def ImportFile(directory,configfile,enc):
    filename = 'empty'
    while '.x' not in filename and '.csv' not in filename:
        fname = input("Enter the name of the file you want to upload (e.g. Project.xls or Project.csv): ")
        filename = directory+fname
        if '.x' in filename:
            sheet = pd.ExcelFile(filename)
            worksheetspresent = sheet.sheet_names
            df = pd.read_excel (filename,WorksheetName(configfile,worksheetspresent),encoding=enc)
            df = df.replace(np.nan,"")              # Replaces NaN (Not a Number) null values with an empty string. This will allow string comparisons in the Children Function
            return df
        elif '.csv' in filename:
            df = pd.read_csv (filename, encoding=enc)
            df = df.replace(np.nan,"")
            return df
        else: 
            print("Error: You can only upload Excel and csv files. Remember to include the extension in the filename (e.g. .xls or .csv)")

# NOT USED YET # Creates a list of the column headers in the dataset. This will be used to check if temporary columns headers are already present. If so, user will be warned that those columns will be overwritten.
def ColumnHeaders(data):
    headers = []                    # Empty list to store column headers.
    for col in data.columns:        # Loops through column headers in dataframe.       
        headers.append(col)         # Appends each column header to a list.
    return headers

# GOOD # This checks if the Reference column contains data, asks if the user minds this being overwritten, and uses boolean to enable program to proceed or stop.
def RefDataCheck(data,Ref):
    if Ref in data.columns:         # This stops the program crashing if the reference column does not exist yet. It is possible for the referece column to be added as a new column.
        spot_data = False
        count = 0
        values = []
        for row in data[Ref]:
            if row != "":
                count += 1
                values.append(row)
                spot_data = True
        if spot_data == True:
            unique_values = set(values)
            user_choice = "blank"
            while user_choice != "Y" and user_choice != "N":
                print()
                print("WARNING:",count,"row(s) in the",Ref,"column contain data. The following values have been found:")
                print("--",unique_values)
                user_choice = input("This data will be overwritten. Do you want to continue? Enter Y/N): ").upper()     # Converts input to upper case to prevent pedantic requirement for user to use uppercase.
                if user_choice == "Y":
                    return True
                elif user_choice == "N":
                    return False
                else:
                    print("You must enter the letter Y or N to continue or stop the program")
        else:
            return True
    else:
        return True             # If the function returns True, it will overwrite the Ref column.

# GOOD # Returns ordered list of levels present in the dataset. This helps with computational efficiency later on.
def ExpectedPresentLevels(data,Lev,configfile):
    Default = DefaultHierarchy(configfile)
    Actual = []
    for row in data[Lev]:
        Actual.append(row)
    LS = set(Actual)
    setlist = []
    for item in Default:                # This for loop ensures that the returned data is ordered in accordance with the archival heierarchy in Levels. Originally I returned the set: LS. But this meant that the reference numbering was out of order, when subsequent functions were using this set
        if item in LS:
            setlist.append(item)
    return setlist

# GOOD # Returns unique unexpected values in level column
def UnexpectedLevels(data,Lev,configfile):
    l = []
    unexpected = []
    for row in data[Lev]:
        l.append(row)
    LS = set(l)
    for item in LS:
        if item not in DefaultHierarchy(configfile):
            unexpected.append(item)
    return unexpected

# GOOD # This provides a list of all items in the levels column.
def PresentLevels(data,Lev):
    Actual = []
    for row in data[Lev]:
        Actual.append(row)
    return set(Actual)

# GOOD # This counts the number of all levels found.
def CountLevels(data,Lev):
    count = 0
    for item in range(len(PresentLevels(data,Lev))):
        count+=1
    return count

# GOOD # Are there unexpected values in Level column True of False?
def LevelBoolean(data,hierarchy):
    flag = False
    for item in data:
        if item not in hierarchy:
            flag = True
    return flag

# GOOD # Enables user to create their own list of hierarchical levels. Returns as a list.
def BuildHierarchy(data,Lev):
    a = "x"
    d = "x"
    hierarchy = []
    while a != "Y" and a != "N":
        a = input("Do you want to build your own hierarchy? Enter Y/N ").upper()
        if a == "Y":
            for i in range(CountLevels(data,Lev)):    # This +1 only works if there is one unexpected value found
                if i == 0:
                    hierarchy.append(input("Enter the top level in the hierarchy: "))
                else:
                    hierarchy.append(input("Enter the next level in the hierarchy: "))                        
        elif a == "N":
            return "Quit"
        else:
            print("You must enter Y or N")
    return hierarchy

#Adds count to all levels in the Hierarchy
def AllLevels(data,Hierarchy,Lev):
    for i in range(len(Hierarchy)):                         # Loops through each level
        LevelName = Hierarchy[i]+"_tempcol"                 # Added "_tempcol" to distinguish it from any columns df that might actually be called "Fonds" etc.
        LevelName = []                                      # Empty list to store reference component or blank string for each row of each column
        count = 0                                           # Counter to produce reference numbers
        for row in data[Lev]:                               # Loops through level column
            rowindex = Hierarchy.index(row)                 # This identifies the index of where the rows level appears in the configured hierarchy list
            if rowindex == i:                               # If the row's level index is == to the index of the level being looped through ...
                count+=1                                    # The counter increments
                LevelName.append("/"+str(count))            # The forward slash and count is added to as a ref component.
            elif rowindex < i:                              # if the index is lower than the level being looped through (if it is a higher hierarchical level)...
                count = 0                                   # The counter is reset to zero becasue we have moved to a higher level
                LevelName.append("")                        # Blank is added because this ref comoponent has already been accouted for i a previous column loop
            elif rowindex > i and count != 0:               # If the index is higher than the level it means this is a child of the previous row and therefore needs its parents ref component.
                LevelName.append("/"+str(count))            # The counter does not increment, but the counter continues to be appended to the column
            else:
                LevelName.append("")
        data[Hierarchy[i]+"_tempcol"] = LevelName           # This adds each list, in turn as a dataframe column
    return data

def Concatenate(data,Hierarchy,Ref,Lev):
    df = pd.DataFrame(data)
    data[Ref] = data["Prefix_tempcol"]                          # Starts the reference by adding the Prefix.
    for i in range(len(Hierarchy)):                                 # This runs the loop for every index in the Levels list
        data[Ref] = data[Ref]+data[(Hierarchy[i]+"_tempcol")]        # This builds the reference by concanating the data from all the present level columns. This relies on b (the Levels function) having an ordered list. Originally I manually typed out the full concatenation of every possible level column. But this created error when a level column wasn't present.
    return data

#
def Bespoke_Delete(unique_child_levels):
    bespoke_delete_child = []                           # List of indexes where user wants to delete children (based on level by level decision).
    bespoke_delete_parent = []                          # List of indexes where user wants to delete parents (based on level by level decision).
    for item_level in unique_child_levels:              # Loops through set of single child levels.
        proceed = input("Level: "+item_level.upper()+" --- Do you want to 'keep', 'delete children', or 'delete parents'? ").upper()   # For each item (level) user asked how they want to proceed
        if proceed == "KEEP":
            continue
        elif proceed == "DELETE CHILDREN":                                         # If user wants to delete children for a particular level ...
            bespoke_delete_child.append(item_level)                                # Adds that level to a list.
        elif proceed == "DELETE PARENTS":                                          # If user wants to delete parents for a particular level ...
            bespoke_delete_parent.append(item_level)                               # Adds that level to a different list.
        else:
            print()
            print("*** WARNING ***")
            print("Invalid answer -- You must enter 'accept', 'delete children', 'delete parents', or 'cancel' ")
            print("*** WARNING ***")
            print("You will be taken back to the first level")
            return Bespoke_Delete(unique_child_levels)   # This loops back through the function if they give an unrecognised answer. Adv: prevents users entering a typo and thinking it worked. Disadv: If they do a typo at the end, they may not realise that the loop will go back to the beginning.
    return bespoke_delete_child,bespoke_delete_parent                                                               # Returns two lists at the end of the loop

# Identifies single chil in the last row of the dataset
def single_child_last_row(data,Hierarchy):
    last_row = data.iloc[[-1]]                  # Creates subset of data containing just the last row.
    for i in range(len(Hierarchy)):             # Loops through each hierarchical column
        for col in last_row[Hierarchy[i]+"_tempcol"]:      # Loops through each row of each column. Because there is only 1 row, it effectively loops through the columns
            if col == "":
                break                           # IF a column row is blank the loop ends. This is because we have reached the last hierarchical level of that row.
            else:
                prev_col = col                  # Stores the column/row value at the end of each loop
    if prev_col == "/1":                        # When the loop ends the prev_col value will be the last value of the hierarchy. If this is /1 it means it is a single child.
        return True                             # Returns True Boolean
    else:
        return False
   

# GOOD # Identifies single children and gives option to remove them.
def Children(data,Hierarchy,Ref,Lev,directory,prefix,enc):
#    import numpy as np
#    import pandas as pd
    flag = False                    # Boolean - Are there single children? True/False.
    singlechildcount=0              # Counts the total number of single children found.
    index = 0                       # This counts and identifies the row number. First row of data = 1 not 0
    singlechildren_firstspot = []
    dfindex = []                    # Will store index of all single children
    parentandchild_index = []       # Will store index of all single children and their parents. This will enable the creation of a subset to be exported for analysis.
    sheetindex = []                 # Will store spreadsheet row number of all single children.
    single_child_end_of_ref = []
    delete_row_list = []            # List of indexes where the row should be deleted (combines children and parent indexes in the 'choose by level' loop)
    for i in range(len(Hierarchy)):                             # This loop counts single children and lists their approximate index numbers
        previousrow = "blank"                                   # Resets the previous row to a neutral value each time the for loop begins iterating over a new level/column.
        index = 0                                               # Resets the index counter to zero each time the for loop begins iterating over a new level/column.
        for row in data[Hierarchy[i]+"_tempcol"]:
            index+=1
            currentrow = row                                    # At the start of each loop, this identifies the row data so that it can be considered in conjunction with the previous row
            if currentrow == "" and previousrow == "/1":
                flag=True                                       # Boolean. True means that at least one single child has been found.
                # Insert if full ref ends in /1 append index, else subtract the last number of ref from the index to give you the accurate row number.
                singlechildren_firstspot.append(index)          # Identifies the rows where the single children are spotted. This might not be the exact row. This will be worked out later.
                singlechildcount+=1                             # Counts the number of single children found
            previousrow = row                                   # At the end of each loop, this identifies the row data so that it can be consisdered in conjunction with the next row.
    if single_child_last_row(data,Hierarchy) == True:                                # If last row of data is a single child ...
        flag = True                                             # Sets single child flag to True
        singlechildren_firstspot.append(index+1)                # Appends spreadsheet row number of last row to list of single children.
        singlechildcount+=1                                     # Adds 1 to the count of single children.
    if flag == False:
        return(data)
    else:                                               # If it finds single children, these are properly identified and the user is informed and asked how they wish to proceed.
        b = []                                          # Empty list to store Yes or "" to indicate whether evey row contains a single child or not
        for a in data['Temp_Index']:                    # This loop identifies the approximate rows that contain single children by comparing the index number to the row number first spotted.
            if a+2 in singlechildren_firstspot:         # This iterates over every row of the df, checking if the df index + 2 is found in the list of approximate row indexes of single children.
                b.append("Yes")                         # If so, it adds yes
            else:                                       # Else it adds blank. This ensures the length of the list is equal to the length of the df columns.
                b.append("")
        data["SingleChild_FirstSpot"] = b               # This creates a column out of the single child yes list. This is how the approximate single child rows are flagged in the df.
        data["SingleChild_FirstSpot"] = np.where((data["SingleChild_FirstSpot"] != ""), data[Ref],"")       # This replaces "Yes" with the catalogue reference numbers.
        for row in data["SingleChild_FirstSpot"]:
            single_child_end_of_ref.append(row.split("/")[-1])          # This splits the spotted reference numbers by forward slash and extracts just the final number of the hierarchy into a new list.
        data["SingleChild_SecondSpot"] = single_child_end_of_ref        # This creates a new column that contains just this last number. This is important for the next for loop.
        data[["Temp_Index", "SingleChild_SecondSpot"]] = data[["Temp_Index", "SingleChild_SecondSpot"]].apply(pd.to_numeric)      # This converts these two columns to numeric values.
        data.loc[data["SingleChild_SecondSpot"] > 1, "ActualIndex"] = data["Temp_Index"] - data["SingleChild_SecondSpot"]    # If the last part of the ref is > 1 this number is subtracted from the df index to find the actual index of the single child.
        data.loc[data["SingleChild_SecondSpot"] == 1, "ActualIndex"] = data["Temp_Index"]                                    # If the  last part of the ref == 1, the df index is also the actual index of the single child [https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.loc.html]
        del data["SingleChild_FirstSpot"]
        del data["SingleChild_SecondSpot"]
        for thingy in data["ActualIndex"]:                      # The values in the Actual Index column are important. The rows they are in is now irrelevant. These values correspond to the values in the dfIndex and the Temp_Index column. 
            if thingy > 0:
                dfindex.append(thingy)                          # This creates a list of all the df indexes of single children. This will later enable the correct df rows to be removed.
                parentandchild_index.append(thingy-1)           # Appends parent index to the single child and parent list
                parentandchild_index.append(thingy)             # Appends child index to the single child and parent list.
                sheetindex.append(thingy+2)                     # This creates a list of all the spreadsheet rows of single children. This will later enable the user to pinpoint the relevant rows on the original spreadsheet.  
        parent_child_subset = data.iloc[parentandchild_index]   # Creates subset of data containing just rows of single children and their parents.
        parent_or_child = []                                    # List to store whether a row is a child or parent
        for item in parent_child_subset["Temp_Index"]:
            if item in dfindex:
                parent_or_child.append("Child")
            else:
                parent_or_child.append("Parent")
        parent_child_subset.insert(loc=1, column='Parent/Child', value=parent_or_child)     # Inserts Pandas column at specified location. https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.insert.html                                             # Once this is working I will replace this with configfile directory.
        if config_boo == True and directory != "":
            sc_and_p_subset_filename = directory+"/"+prefix+"_"+time_stamp+"_SingleChildrenAndParents.csv"
        else:
            sc_and_p_subset_filename = prefix+"_"+time_stamp+"_SingleChildrenAndParents.csv"
        parent_child_subset.to_csv(sc_and_p_subset_filename, index = False, encoding = enc)                                       
        singlechilddict = {}            # Dictionary to store all single child indexes and their corresponding levels.
        Level_Index_Dict = {}           # Dictionary to store all single child levels and a corresponding list of levels (a reverse of singlechilddict).
        child_levels = []               # List to store levels of single children
        for child in dfindex:                                                                   # Loops through list of single child indexes.
            child_levels.append(data.loc[(data["Temp_Index"] == child),Lev].iloc[0])        # Appends the levels of single children to a list. [https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.iloc.html#pandas.DataFrame.iloc]
            singlechilddict[child] = data.loc[(data["Temp_Index"] == child),Lev].iloc[0]    # Creates dictionary key for each index number and adds corresponding level as its value.
        unique_child_levels = set(child_levels)                                                 # Converts list of single child levels to a set of unique values.
        child_sheet_index = {}
        for item_level in unique_child_levels:                      # Loops through set of single child levels.
            item_list_index = "item_list_index_"+item_level         # Creates unique variable name for each level in the loop (for indexes).
            item_list_index = []                                    # Assigns that a variable name as an empty list. This will store a list of indexes associated with that level.
            item_list_sheetrow = "item_list_sheetrow_"+item_level   # Creates unique variable name for each level in the loop (for spreadsheet row numbers).
            item_list_sheetrow = []                                 # Assigns that a variable name as an empty list. This will store a list of spreadsheet row numbers associated with that level.
            for key, value in singlechilddict.items():              # Loops through the keys in the dictionary of indexes (key) and their level (value).
                if value == item_level:                             # If the value (level) in the dictionary matches the item (level) in the list ...
                    item_list_index.append(key)                     # It appends the corresponding key (index) to a list of indexes assoaciated with that item (level).
                    item_list_sheetrow.append(int(key+2))                # It appends the corresponding spreadsheet row number associated with that item (level).
                Level_Index_Dict[item_level] = item_list_index          # Creates dictionary key for each item (level) and adds the list of corresponding single child indexes as its value.
                child_sheet_index[item_level] = item_list_sheetrow  # Creates dictionary key for each item (level) and adds the list of corresponding single child indexes as its value.
        print()
        print("WARNING:",singlechildcount,"single-child record(s) have been found. The following spreadsheet rows are single-child records.")     # This tells the user how many rows are single children. It also identifies the spreadsheet row numbers so the user can go back to the original sheet to investigate.
        for k, v in child_sheet_index.items():      # Prints key (level) and then list of values (spreadsheet row numbers).
            print("*",k,"--",v)
        print()
        print("Subset of single children and their parents exported to the following location:",sc_and_p_subset_filename)
        proceed = "x"
        if config_boo == True and directory != "":
            deleted_subset_filename = directory+"/"+prefix+"_"+time_stamp+"_Deleted_Rows.csv"                      # Creates a filename and directory location for the deleted rows subset.                                       # This assigns a neutral value to allow the while loop to begin.
        else:
            deleted_subset_filename = prefix+"_"+time_stamp+"_Deleted_Rows.csv" 
        while proceed != "KEEP" and proceed != "DELETE CHILDREN" and proceed != "DELETE PARENTS" and proceed != "CHOOSE BY LEVEL" and proceed != "CANCEL":          # The user must decide whether to accept or delete the rows with missing children.
            proceed = input("Do you want to 'delete children', 'delete parents', 'keep' the single child rows, or 'Choose by Level'? To stop the program enter 'cancel' ").upper()
            if proceed == "KEEP":             # If accepted, the single children are kept.
                del data["ActualIndex"]
                return(data)
            elif proceed == "CANCEL":           # This option is so that the user can cancel the program, clean the data, and start again.
                print("The program has finished without generating any references.")
                sys.exit()
            elif proceed == "DELETE CHILDREN":           # This option will delete the single children rows and re-run the generation of catalogue references.
                for c in data["ActualIndex"]:   # find rows, delete them, then redo ref calculations.
                    if c in dfindex:
                        d = int(c)              # This converts the data into integers
                        delete_row_list.append(d)
                deleted_rows_subset = data.iloc[delete_row_list]                                        # Creates a subset dataframe containing just the rows that have been deleted.
                deleted_rows_subset.to_csv(deleted_subset_filename, index = False, encoding = enc)       # Exports deleted rows subset as a csv file.
                newdata = data.drop(delete_row_list)          # This creates a new version of the df but with the single child rows deleted. It does this by matching the integers in the e list to the df index.
                del newdata["ActualIndex"]
                return Concatenate(AllLevels(newdata,Hierarchy,Lev),Hierarchy,Ref,Lev)          # This re-does the reference generation on the new df and concatenates the references. Initially the returned data still contained deleted rows -- Fixed by putting this function as an argument within the next function
            elif proceed == "DELETE PARENTS":
                singlechilddict = {}            # Empty dictionary to store single child indexes and thier original level
                parentdict={}                   # Empty dictionary to store the indexes of parents with single children and their original indexes
                for singlechild in dfindex:     # Loops through list of single child indexes
                    singlechilddict[singlechild] = data.loc[(data["Temp_Index"] == singlechild),Lev].iloc[0]       # Adds index of single children as key and corresponding level as value
                    parentdict[singlechild-1] = data.loc[(data["Temp_Index"] == singlechild-1),Lev].iloc[0]        # Adds index of parents of single children as key and corresponding level as value
                    data.loc[data["Temp_Index"] == singlechild,Lev] = parentdict[singlechild-1]                   # Uses dictionary above to change level of child with level of parent. This will ensure the reference is at the same hierarchical level.
                for c in data["ActualIndex"]:   # find rows, delete them, then redo ref calculations.
                    if c in dfindex:
                        d = int(c)-1            # This converts the data into integers
                        delete_row_list.append(d)
                deleted_rows_subset = data.iloc[delete_row_list]                                        # Creates a subset dataframe containing just the rows that have been deleted.
                deleted_rows_subset.to_csv(deleted_subset_filename, index = False, encoding = enc)       # Exports deleted rows subset as a csv file.
                newdata = data.drop(delete_row_list)          # This creates a new version of the df but with the single child rows deleted. It does this by matching the integers in the e list to the df index.
                del newdata["ActualIndex"]
                newdata_withnewrefs = Concatenate(AllLevels(newdata,Hierarchy,Lev),Hierarchy,Ref,Lev)
                for sin_child in dfindex:
                    newdata_withnewrefs.loc[newdata_withnewrefs["Temp_Index"] == sin_child,Lev] = singlechilddict[sin_child]       # Uses dict above to reassign the original level to the child row.
                return newdata_withnewrefs            
            elif proceed == "CHOOSE BY LEVEL":
                delete_children, delete_parents = Bespoke_Delete(unique_child_levels)   # Assigns variables to the two returned values
                for item in delete_children:                                            # Loops through list of levels where child rows should be deleted.
                    for key, value in Level_Index_Dict.items():                         # Loops through the keys in the dictionary of levels (key) and their values (list of indexes).
                        if key == item:                                                 # If the key (level) matches the item (level)...
                            for index_to_be_deleted in value:                           # Loops through indexes in list of values for that each key (level)
                                delete_row_list.append(index_to_be_deleted)             # Appends those indexes to a new list. This will be a complete list of indexes for all child rows to                     
                delete_parent_list = []
                for item in delete_parents:                                             # See previous for loop for explanation (this is the parent equivalent)
                    for key, value in Level_Index_Dict.items():
                        if key == item:
                            for thing in value:
                                delete_row_list.append(thing-1)
                                delete_parent_list.append(thing)                        # Appends the index of children whose parents are to be deleted.
                singlechilddict = {}                 # Empty dictionary to store single child indexes and thier original level
                parentdict={}                        # Empty dictionary to store the indexes of parents with single children and their original indexes
                for child in delete_parent_list:     # Loops through list of single child indexes
                    singlechilddict[child] = data.loc[(data["Temp_Index"] == child),Lev].iloc[0]    # Adds index of single children as key and corresponding level as value
                    parentdict[child] = data.loc[(data["Temp_Index"] == child-1),Lev].iloc[0]             # Adds index of parents of single children as key and corresponding level as value
                    data.loc[data["Temp_Index"] == child, Lev] = parentdict[child]                 # Uses dictionary above to change level of child with level of parent. This will ensure the reference is at the same hierarchical level.
                newer_data = data.drop(delete_row_list)                 # Creates a new version of the data with the selected rows deleted (dropped)
                del newer_data["ActualIndex"]
                newer_data_withnewrefs = Concatenate(AllLevels(newer_data,Hierarchy,Lev),Hierarchy,Ref,Lev)
                for child in delete_parent_list:
                    newer_data_withnewrefs.loc[newer_data_withnewrefs["Temp_Index"] == child, Lev] = singlechilddict[child]     # Uses dict above to reassign the original level to the child row.
                deleted_rows_subset = data.iloc[delete_row_list]                                        # Creates a subset dataframe containing just the rows that have been deleted.
                deleted_rows_subset.to_csv(deleted_subset_filename, index = False, encoding = enc)       # Exports deleted rows subset as a csv file.
                return(newer_data_withnewrefs) 
            else:
                print("You must enter 'keep', 'delete children', 'delete parents','choose by level', or 'cancel' ")            # This reminds the user that they have 4 options to exit the while loop.
        print(delete_row_list)

def Prefix(data,prefix,Lev):
    prefix_col = []
    for row in data[Lev]:
        prefix_col.append(prefix)
    data["Prefix_tempcol"] = prefix_col
    return(data)

def FolderName(directory,prefix,configfile):
    if config_boo == True and configfile["OutputFilepath"] != "" and configfile["OutputPathUsePrefix"].upper() == "YES":
        NameStart = prefix+" "
        folder_list = [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]      # returns list of folders in specified directory
        for thing in folder_list:
            if NameStart in thing or prefix == thing:
                a = directory+"/"+thing           # Returns name of the folder to enter, based on the EAP ref (prefix)
                break
            else:
                a = directory
        return a
    elif config_boo == True and configfile["OutputFilepath"] != "" and configfile["OutputPathUsePrefix"].upper() == "NO":
        return directory
    elif config_boo == False or configfile["OutputFilepath"] == "":
        return directory
    else:
        print("ERROR: Check the configuration file (RefGenConfig.json). Check 'OutputFilepath' is correct. Also check that 'OutputPathUsePrefix' is set to either Yes or No.")
        

# Concatenates reference and exports csv
def output(df,b,prefix,Ref,Lev,Directory,configfile,enc):
    df[Ref] = df["Prefix_tempcol"]                          # Starts the reference by adding the Prefix.
    del df["Prefix_tempcol"]                                # This deletes the temporary prefix column, which is now obsolete
    del df["Temp_Index"]                                    # This deletes the temporary index column
    for i in range(len(b)):                                 # This runs the loop for every index in the Levels list
        df[Ref] = df[Ref]+df[(b[i]+"_tempcol")]                        # This builds the reference by concanating the data from all the present level columns. This relies on b (the Levels function) having an ordered list. Originally I manually typed out the full concatenation of every possible level column. But this created error when a level column wasn't present.# https://datatofish.com/concatenate-values-python/ showed me how to concatenate.
        del df[(b[i]+"_tempcol")]                                      # This uses the index to ensure that every present level column is deleted. I NEED TO FIX THIS SO THAT IT ONLY APPLIES TO PRESENT LEVELS.
    print()
    if config_boo == True and configfile["OutputFilepath"] == "":                             # If config file exists, that provides the default hierarchy.
        if configfile["OutputFormat"].upper() == "EXCEL" or configfile["OutputFormat"].upper() == "XLSX" or configfile["OutputFormat"].upper() == ".XLSX":           # The user can select .xlsx as the output format
            newfilename = prefix+"_"+time_stamp+"_RefsGenerated.xlsx"
            print(newfilename,"successfully generated in the same folder location as this application.")
            return df.to_excel(newfilename, index = False, encoding = configfile["Encoding"])
        elif configfile["OutputFormat"].upper() == "XLS" or configfile["OutputFormat"].upper() == ".XLS":
            newfilename = prefix+time_stamp+"_"+"_RefsGenerated.xls"
            print(newfilename,"successfully generated in the same folder location as this application.")
            return df.to_excel(newfilename, index = False, encoding = configfile["Encoding"])
        elif configfile["OutputFormat"].upper() == "XLSM" or configfile["OutputFormat"].upper() == ".XLSM":
            newfilename = prefix+"_"+time_stamp+"_RefsGenerated.xlsm"
            print(newfilename,"successfully generated in the same folder location as this application.")
            return df.to_excel(newfilename, index = False, encoding = configfile["Encoding"])
        else:                                              # The default value is csv.
            newfilename = prefix+"_"+time_stamp+"_RefsGenerated.csv"
            print(newfilename,"successfully generated in the same folder location as this application.")
            return df.to_csv(newfilename, index = False, encoding = configfile["Encoding"])
    elif config_boo == True and configfile["OutputFilepath"] != "":                             # If config file exists, that provides the default hierarchy.
        if configfile["OutputFormat"].upper() == "EXCEL" or configfile["OutputFormat"].upper() == "XLSX" or configfile["OutputFormat"].upper() == ".XLSX":           # The user can select .xlsx as the output format
            newfilename = Directory+"/"+prefix+"_"+time_stamp+"_RefsGenerated.xlsx"
            print("File successfully generated in the following location:",newfilename)
            return df.to_excel(newfilename, index = False, encoding = configfile["Encoding"])
        elif configfile["OutputFormat"].upper() == "XLS" or configfile["OutputFormat"].upper() == ".XLS":
            newfilename = Directory+"/"+prefix+"_"+time_stamp+"_RefsGenerated.xls"
            print("File successfully generated in the following location:",newfilename)
            return df.to_excel(newfilename, index = False, encoding = configfile["Encoding"])
        elif configfile["OutputFormat"].upper() == "XLSM" or configfile["OutputFormat"].upper() == ".XLSM":
            newfilename = Directory+"/"+prefix+"_"+time_stamp+"_RefsGenerated.xlsm"
            print("File successfully generated in the following location:",newfilename)
            return df.to_excel(newfilename, index = False, encoding = configfile["Encoding"])
        else:                                              # The default value is csv.
            newfilename = Directory+"/"+prefix+"_"+time_stamp+"_RefsGenerated.csv"
            print("File successfully generated in the following location:",newfilename)
            return df.to_csv(newfilename, index = False, encoding = configfile["Encoding"]) 
    else:
        newfilename = prefix+"_"+time_stamp+"RefsGenerated.csv"
        print(newfilename,"successfully generated in the same folder location as this application.")
        return df.to_csv(newfilename, index = False, encoding = "utf-8-sig")    # creates csv file from pandas df. If I have time I will look into the hard way of exporting as a csv

def RefGenerator():
    EnterPrefix = input("Enter the reference prefix (e.g. the EAP project number): ")
    ActualPrefix = EnterPrefix
    if ConfigBoolean() == True:
        configfile = ImportConfigFile()                 # Stored config file as a variable to avoid repeated calling of the config file. This uses only marginal memory.
        if configfile["RefGenColumnName"] != "":
            Ref = configfile["RefGenColumnName"]
        else:
            Ref = "Reference"
        if configfile["HierarchyColumnName"]:
            Lev = configfile["HierarchyColumnName"]
        else:
            Lev = "Level"
        if configfile["Encoding"] != "":
            enc = configfile["Encoding"]
        else:
            enc = "utf-8-sig"
        importdir = configfile["ImportFilepath"]
        exportdir = configfile["OutputFilepath"]
    else:
        Ref = "Reference"
        Lev = "Level"
        configfile = ""
        importdir=""
        exportdir = ""
        enc = "utf-8-sig"
    importdirectory = ImportFilePath(importdir,ActualPrefix,configfile)
    folder_directory = FolderName(exportdir,ActualPrefix,configfile)
    data = ImportFile(importdirectory,configfile,enc)
    column_heads = ColumnHeaders(data)
    if Lev not in column_heads:
        column_dict = {}
        col_count = 0
        print()
        print("*** NOTIFICATION: List of column names in dataset***")
        for header in column_heads:
            col_count +=1
            column_dict[str(col_count)] = header
            print(col_count,"-",header[0:50])
        while Lev not in column_heads:
            print()
            print('*** WARNING *** The data set does not contain a column called: "'+Lev+'"')
            Lev_Choice = input("Enter the number of the column containing the hierarchy data (see numbered list of column headers above): ")
            Lev = column_dict[Lev_Choice]
    if RefDataCheck(data,Ref) == False:
        sys.exit()
    else:
        data.insert(loc=0, column='Temp_Index', value=data.index)   # Creates a new column containing the pandas index number for each row [0 onwards]                              
        Prefix(data,ActualPrefix,Lev)
        if LevelBoolean(UnexpectedLevels(data,Lev,configfile),DefaultHierarchy(configfile)) == True:
            clean_levels = "empty"
            level_boo = True
            while level_boo == True:
                print()
                print("NOTIFICATION: Expected item(s) in Levels column listed below: ")
                print(ExpectedPresentLevels(data,Lev,configfile))
                print()
                print("ERROR: Unexpected item(s) found in Levels column. Unexpected items listed below:")
                print(UnexpectedLevels(data,Lev,configfile))
                while clean_levels != "Y" and clean_levels != "N":
                    clean_levels = input("Do you want to amend the unexpected levels? Y/N ").upper()
                    if clean_levels == 'Y':
                        updated_levels = []
                        for item in UnexpectedLevels(data,Lev,configfile):
                            new_level = input("** "+item+" ** What do you want to replace this with? ")
                            data[Lev] = np.where((data[Lev] == item), new_level, data[Lev]) 
                        if LevelBoolean(UnexpectedLevels(data,Lev,configfile),DefaultHierarchy(configfile)) == False:
                            Hierarchy = ExpectedPresentLevels(data,Lev,configfile)
                            level_boo = False
                        else:
                            clean_levels = "empty"
                            print()
                            print("NOTIFICATION: There are still unexpected item(s) in Levels column listed below: ")
                            print(ExpectedPresentLevels(data,Lev,configfile))
                            print()
                            print("ERROR: Unexpected item(s) found in Levels column. Unexpected items listed below:")
                            print(UnexpectedLevels(data,Lev,configfile))
                    elif clean_levels == 'N':
                        Hierarchy = BuildHierarchy(data,Lev)
                        if Hierarchy == "Quit":
                            level_boo = False
                            clean_levels = "N"
                            sys.exit()
                        else:
                            level_boo = LevelBoolean(UnexpectedLevels(data,Lev,configfile),Hierarchy)
                            if level_boo == True:
                                clean_levels = "empty"
                                print()
                                print("NOTIFICATION: Expected item(s) in Levels column listed below: ")
                                print(ExpectedPresentLevels(data,Lev,configfile))
                                print()
                                print("ERROR: Unexpected item(s) found in Levels column. Unexpected items listed below:")
                                print(UnexpectedLevels(data,Lev,configfile))
                                print()
                                print("This is your current hierarchy: ")
                                print(Hierarchy)
                    else:
                        print("You must enter Y or N")
        else:
            Hierarchy = ExpectedPresentLevels(data,Lev,configfile)
        if Hierarchy == "Quit":
            sys.exit()
        else:
            AllLevels(data,Hierarchy,Lev)
            Concatenate(data,Hierarchy,Ref,Lev)
            output(Children(data,Hierarchy,Ref,Lev,folder_directory,ActualPrefix,enc),Hierarchy,ActualPrefix,Ref,Lev,folder_directory,configfile,enc)
            return(data)

RefGenerator()
