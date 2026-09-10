-- Version specific base addresses.
-- Verified by disassembling both shipped executables:
--   Stronghold_Crusader_Extreme.exe and Stronghold Crusader.exe
-- Everything else in this module is located through AOB scans (see init.lua);
-- the current-unit-id global is read straight out of the tick-hook AOB match.
if data.version.isExtreme() then
    return {
        unit_array_base_addr = 0x145D03C,
        max_units = 10000,
    }
else
    return {
        unit_array_base_addr = 0x138854C,
        max_units = 2500,
    }
end
