param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ProfileName
)

instaloader profile $ProfileName --reels +args.txt
