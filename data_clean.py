# Create a list to stored the bad links
removeList = []

# Process the badlist to extract the entry num of bad link
with open('dump/clean_0126_013744/bad.list', 'r') as badList:
    for line in badList:
        elements = line.split('/')
        entryNum = elements[-1].split('-')
        removeList.append(entryNum[0])


# Counter for entry num in origin list
count = 1

# Use the origin list as the source to make a cleaned list
with open('sites/Tranco_23Dec_21Jan_2021_top30k_filtered_cp.list', 'r') as siteList, open('sites/cleaned_sites.list', 'w+') as cleanedList:
    for line in siteList:
        if not str(count) in removeList:
            cleanedList.write(line)
        count += 1
