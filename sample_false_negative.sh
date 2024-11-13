#!/bin/bash

echo "Running final.py on Sample False Negative => Issue in Parity of 'z'"
echo
echo
python final.py sample_false_negative.py
echo
echo "-------------------------"
echo "The parity of 'z' is TOP but it should be ODD due to the line 'z=z+1'"
echo "Finished parity analysis"
echo "-------------------------"
echo
echo

