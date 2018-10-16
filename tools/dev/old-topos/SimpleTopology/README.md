# Setup Scripts

These scripts will set up and run an ONOS controller on the local machine with a simple mininet topology. You will be prompted to make sure that the components are loaded in the correct order. If anything stops working, run cleanup and then setup again in run.sh.

1. Make sure *$ONOS_ROOT* is set to the ONOS root directory.
2. Make sure *$ONOS_USER* and *$ONOS_GROUP* are set to something (usually both hostname) in the bash profile.
3. Make sure the snortPorts hashmap in SnortManager.java in the Snort App contains variables according to your topology.
4. Set the variables in run.sh.
  * Set the location ONOS service will be unpacked and ran by changing *ONOS_SERVICE* (/tmp by deafult).
  * Set the location of the Mervyn Controller by changing *MERVYN_CONTROL*.
  * Set the location of the ONOS-Mervyn Apps folder by changing *MERVYN_APPS*.
  * Set the location of PigRelay by changing *PIGRELAY*.
5. Set up mervyn and pigrelay configs in the config folder.
  * The config files should be set up to run with the pre-made topologies.
  * Change the thresholds in thresholds.yaml if you want. Remember that the 'rule' field is a snort rule.
6. Build ONOS with mvn clean install (only needed once).
7. Run "bash run.sh".
  * Setup only needs to be run the first time and after a cleanup.
  * Components must be started in the order ONOS->(Apps/(Mininet->Pigrelay))->Mervyn.
  * Cleanup can be done at the end of the session and will leave it how it was at the start.
8. (Optional) When mininet has started, use the command "source runEval" to ping and iperf between all hosts.


Inside mininetTopo.py, there is a commented out topology which can be used instead, just uncomment, follow the instructions and comment out the old topology.

If you change the location of snort in the mininet topology, make sure to change the config files for mervyn and pigrelay in the config/mervyn and config/pigrelay folders. Also, make sure to change the pair in snortPorts so each switch knows the port to output to Snort.

If you change the tables used make sure to change them in SnortManager.java and SecurityPipeline.java
