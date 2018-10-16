i="0"
while [ $i -lt $3 ];
	do (top -bn 1 | awk '{ printf("%f %f %s\n", $9, $10, $12); }' | grep $1 | awk -v cmd="$1" -F ' ' '$3 == cmd {cpuSum += $1; memSum += $2} END {printf("%f %f\n"), cpuSum, memSum}')  >> $2; 
	sleep 1;
	i=$((i+1))
done;
