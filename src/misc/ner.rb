#!/usr/bin/env ruby
path = ""
if File.directory?(ARGV.first)
  path = File.expand_path(ARGV.first)
end

Dir[File.join(path, "*.txt")].each do |file|
  new = File.basename(file, File.extname(file))
  system("/Users/dan/attic/tools/nlp/ner/stanford-ner-2013-06-20/ner #{file} > tmp/#{new}.ner")
#  system("/Users/dan/attic/tools/stanford-ner-2013-06-20/ner #{file} > tmp/#{new}.ner")
end
