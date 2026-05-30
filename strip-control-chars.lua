-- strip-control-chars.lua
-- Remove ASCII control characters (0x00-0x08, 0x0B-0x1F, 0x7F) from text content.
-- Preserves tab (0x09), newline (0x0A), carriage return (0x0D).
local CTRL = "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"

function Str(el)
  el.text = el.text:gsub(CTRL, "")
  return el
end

function Code(el)
  el.text = el.text:gsub(CTRL, "")
  return el
end

function CodeBlock(el)
  el.text = el.text:gsub(CTRL, "")
  return el
end
