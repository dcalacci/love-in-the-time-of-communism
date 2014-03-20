# scripts

classifier.py is where all the magic happens

testimonyUtils.py is where all the preprocessing happens.

To run classifer.py (and to compute scores for particular entities),
make sure that you have the stanford NER processor running in socket
mode on your local machine: 

``` bash
java -mx1000m -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer 
    -loadClassifier classifiers/english.muc.7class.distsim.crf.ser.gz 
    -port 8080 -outputFormat inlineXML
```
