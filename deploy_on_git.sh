#!/bin/bash

usage() {
  echo "Usage: $0 -v <version> -c <commit comment> [-t <optional1>] "
  echo "  -v <version>            Specify the version (major, minor, patch, overwrite). Required."
  echo "  -c <comment commit>     Specify comment to the commit. Required"
  echo "  -t <tag description>    Specify tag description.(New tag is publishing)"

  exit 1
}

# Function to ask for confirmation
confirm() {
  read -p "Are you sure you want to continue? (y/n): " response
  if [[  "$response" != "y" && "$response" != "Y" ]]; then
    echo "[WRN] Script execution aborted."
    exit 1
  fi
}

while getopts "v:t:c:" opt; do
  case $opt in
    v)
      version="$OPTARG"
      ;;
    c)
      commit_note="$OPTARG"
      ;;
    t)
      tag_description="$OPTARG"
      ;;
    \?)
      echo "[WRN] Invalid option: -$OPTARG" >&2
      usage
      ;;
  esac
done

# Check if the version flag is not provided
if [ -z "$version" ]; then
  echo "[INFO] Version flag (-v) is required."
  usage
fi

# Check if the version is valid
if [[ "$version" != "major" && "$version" != "minor" && "$version" != "patch" && "$version" != "overwrite"  ]]; then
  echo "[INFO] Invalid version. Type (https://semver.org/) or incorrect type specified, try: -v [major, minor, patch, overwrite]"
  usage
fi


# get highest tag number, and add 1.0.0 if doesn't exist
current_Version=`git describe --abbrev=0 --tags 2>/dev/null`

if [[ $current_Version == '' ]]
then
  current_Version='0.0.1'
fi



# Print the provided parameters
echo "  Deploy on Github:"
echo "  to do......................: $version"
echo "  comment for the new commit.: $commit_note"
echo "  tag description(optional)..: $tag_description"
echo "  current version............: $current_Version"



# replace . with space so can split into an array
current_Version_PARTS=(${current_Version//./ })

# get number parts
vNum1=${current_Version_PARTS[0]}
vNum2=${current_Version_PARTS[1]}
vNum3=${current_Version_PARTS[2]}
vOverwrite=0

if [[ $version == 'major' ]]
then
  vNum1=$((vNum1+1))
  vNum2=0
  vNum3=0
elif [[ $version == 'minor' ]]
then
  vNum2=$((vNum2+1))
  vNum3=0
elif [[ $version == 'patch' ]]
then
  vNum3=$((vNum3+1))
elif [[ $version == 'overwrite' ]]
then
  vOverwrite=1
  echo "[INFO] no new version required. overwrite last version"
else
  echo "[INFO] no version type (https://semver.org/) or incorrect type specified, try: -v [major, minor, patch, overwrite]"
  exit 1
fi

#create new tag
vForced_comment=0
if [[ "$vOverwrite" == 0 ]];
then

  New_Tag="$vNum1.$vNum2.$vNum3"
  echo "[INFO] ($version) updating $current_Version to $New_Tag"
  if [ ! -n "$commit_note" ]; then
    # echo "comment provide"
    commit_note="updating $current_Version to $New_Tag"
    vForced_comment=1
  fi
else

  echo "[INFO] ($version) updating the current version $current_Version"
  if [ ! -n "$commit_note" ]; then
    commit_note="update current version $current_Version"
    vForced_comment=1
  fi
fi

if [[ vForced_comment == 1 ]]; then
  echo "[INFO] comment for the commit(forced)........: $commit_note"
fi

# Ask for confirmation
confirm

# Continue with the script
echo "[INFO] Continuing with the script..."



### yarn version --new-version $New_Tag --no-git-tag-version
echo "[INFO] Git add"
git add .
echo "[INFO] Git commit"
git commit -m "$commit_note"

if [[ "$vOverwrite" == 0 ]];
then
  echo "[INFO] Git rev-parse"
  # get current hash and see if it already has a tag
  git_commit_cmd=`git rev-parse HEAD`

  echo "[INFO] Git describe"
  # NEEDS_TAG=`git describe --contains $git_commit_cmd 2>/dev/null`
  Need_Tag=`git describe --contains $git_commit_cmd`

  echo "[INFO] Git describe:   $Need_Tag"
else
  echo "[INFO] skip git rev-parse and describe command"
  $Need_Tag = "no-new"
fi

if [ -z "$Need_Tag" ];
then
  # yarn version --new-version $New_Tag --no-git-tag-version
  if [[ "$vOverwrite" == 0 ]];
  then
    echo "[INFO] Tagged with:   $New_Tag"
    git tag $New_Tag

    echo "[INFO] Git tags:  "
    git push --tags
  fi
  echo "[INFO] Git push:  "
  git push # origin main  # o master
else
  echo "[INFO] Already a tag on this commit"
  exit 1
fi

echo "[INFO] end procedure"

exit 0