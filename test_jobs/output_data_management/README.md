title: DIRAC "OutputSandbox" README

Introduction
============

This example goes a little deeper into submitting jobs using dirac. Here a file called ```env.out``` is created from the ```env``` command. This file will be placed in the output sandbox

Submission
==========

To submit the job, you use the python executable

```bash
./OutputSandbox.py > OutputSandbox.out
```

Job Status
==========

You can view the job status using

```bash
dirac-wms-job-status JID
````
where JID is the job ID in the .out file

Output
======

Once you have confirmed the job has completed, you can download the output data using DIRAC

```bash
$ dirac-wms-job-get-output -D ./ ```cat OutputSandboxTest.jid```
Job output sandbox retrieved in ./15004727/
$ ls 15004727
env.out
std.out
job.log
$ wc -l JID/env.out
161 JID/env.out
```

