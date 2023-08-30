#Creating a program for backing up files from a directory to an app folder in dropbox automatically. 
#To do so, bring the desired files to the "files" folder or replace the files folder entirely and also replace the "files" literal everywhere
#We will be using the f string literal in order to designate the path, read() to read all the data, the "rb" or read-bytes method
import os
import dropbox
import dropbox.files
import hashlib

with open("accessToken.txt","r") as fil:
    access_token = fil.read()

dbx = dropbox.Dropbox(access_token)

def uploadFiles():
    #Iterating for all entries in our "files" folder locally
    for file in os.listdir("files"):
        #In the brackets we pass the directory name which is "files" in this case AND the file itself which we have currently assigned to "file"
        with open(os.path.join("files", file),"rb") as f:
            #We read all the data and upload it to the file we pass as f string to show a definite path
            info = f.read()
            dbx.files_upload(info, f"/{file}")

def downloadFiles():
    #Iterating for entries in the cloud - Going thru entries we can find remotely in the file list and download
    #every individual file to our local directory called "files" in this situation with the specific entry name and
    #we use f string literal to store it locally with same file name
    for entry in dbx.files_list_folder("").entries:
        dbx.files_download_to_file(os.path.join("files",entry.name),f"/{entry.name}")

'''
The above code so far allows entire upload and download but that is not always reasonable and we may need only 
few select data/files
To execute this selective upload and download we use the content_hash metadata which we can find when we print the 
metadata using the following script:

for entry in dbx.files_list_folder("").entries:
    print(entry)

For reference, hash is a one way function where you input something and get an output of fixed size and is irreversible
Dropbox has particular content hashes so we use the hashlib module here
Basically, we are gonna check if there's any change in the metadata of our local files and the entries in the cloud

Dropbox creates its own contentHashes using the following method so we are going to apply their own technique
They do multiple hashes on different chunks and then append them.
We are gonna replicate their contentHash creation method using the function created below and we can test it by printing the value we get upon passing a file in our local directory thru the function we created
'''

def dbx_content_hash(file):
    #Dropbox initializes their chunksize to 4 times the square of 1024
    hashChunkSize = 4*1024*1024
    with open(file, "rb") as c:
        #Initializing blockHashes with zero bytes
        blockHashes = bytes()
        while True:
            #Reading hashChunksSize and assigning it to a variable called chunk
            chunk = c.read(hashChunkSize)
            #If we do not have a chunk, we just break the loop
            if not chunk:
                break
            #sha256 is an algorithm used to create a unique hash for the files that go through this function.
            #Both digest and hexdigest are used to return encoded hash but they are different in their formats. 
            #We use sha256 on a chunk rather than the whole file and we append it
            blockHashes = blockHashes + hashlib.sha256(chunk).digest()
        return hashlib.sha256(blockHashes).hexdigest()

#The next functions we are about to create is used to replace local directory files using files from the cloud if they are different AND to upload files that are not there in the cloud but in the local directory
def changedFileDownload():
    for entry in dbx.files_list_folder("").entries:
        if os.path.exists(os.path.join("files", entry.name)):
            localFileHash = dbx_content_hash(os.path.join("files", entry.name))
            #If there is a change in content hash, there is a change in the file
            if localFileHash != entry.content_hash:
                print("Change in file: ", entry.name)
                dbx.files_download_to_file(os.path.join("files", entry.name), f"/{entry.name}")
            else:
                print("No change: ", entry.name)
        #As path does not exist, we can consider it to be a new file
        else:
            print("New File: ", entry.name)
            dbx.files_download_to_file(os.path.join("files", entry.name),f"/{entry.name}")

def changedFileUpload():
    #We are making cloudFiles a dictionary of entries in the cloud AND the colon after the first passed value denotes that the first passed value is a key to the dictionary, ent.name is also the file name.
    cloudFiles = {ent.name: ent.content_hash for ent in dbx.files_list_folder("").entries}
    for file in os.listdir("files"):
        #The keys here are the entry names
        if file in cloudFiles.keys():
            localHash = dbx_content_hash(os.path.join("files", file))
            #Getting value for file name or ent.name in this case gives us the content hash
            if localHash != cloudFiles[file]:
                print("Change in file: ", file)
                with open(os.path.join("files", file), "rb") as j:
                    info = j.read()
                    #Path  to upload data is going to be just the file name in this case
                    #Overwrite as the write mode for the upload function allows us to overwrite the existing files
                    dbx.files_upload(info, f"/{file}", mode = dropbox.files.WriteMode("overwrite"))
            else:
                print("No change: ", file)
        #Same technique as before. If the file doesn't exist then we just upload it considering it as a new file
        else:
            print("New File: ", file)
            with open(os.path.join("files", file),"rb") as j:
                info = j.read()
                dbx.files_upload(info, f"/{file}", mode = dropbox.files.WriteMode("overwrite"))