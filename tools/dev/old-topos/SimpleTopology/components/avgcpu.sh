i="0"
while [ $i -lt $3 ];
	do (ps -C $1 -o pcpu,pmem | tail -n1 | grep -v CPU ) >> $2; 
	sleep 1;
	i=$((i+1))
done;
