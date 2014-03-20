#!/usr/bin/env ruby
require "docsplit"

path = ""
if File.directory?(ARGV.first)
  path = File.expand_path(ARGV.first)
end

docs = Dir[File.join(path, "*.pdf")]
Docsplit.extract_text(docs, :output => 'storage/text')
