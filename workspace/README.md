# auto classification

## The classification process

if file in workspace directory

1. if the file is larger than 10MB, skip it
2. check if it's exists based on md5
3. if not, try to use .github/catalog, and call AI to classify it and copy it to the corresponding directory
4. if still not classified, ask human curator to classify it

rename the workspace dir to old_workspace.

And then run the script to update the database.
