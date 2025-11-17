import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

export type AttackType = 'DDos' | 'XSS/SQL Injection' | 'Port Probing' | 'Brute Force' | 'Sloworis';

type Props = {
    value: AttackType;
    onChange: (v: AttackType) => void;
};

export default function AttackSelector({value, onChange}: Props) {
    return (
        <FormControl size= "small" sx={{minWidth:180}}>
            <InputLabel id="attack-type-label">Attack Type</InputLabel>
            <Select
                labelId="attack-type-label"
                value={value}
                label="Attack Type"
                onChange={(e) => onChange(e.target.value as AttackType)}
                >
                    <MenuItem value = "DDos">DDos</MenuItem>
                    <MenuItem value = "XSS/SQL Injection">XQL/SQL Injection</MenuItem>
                    <MenuItem value = "Port Probing">Port Probing</MenuItem>
                    <MenuItem value = "Brute Force">Brute Force</MenuItem>
                    <MenuItem value = "Sloworis">Sloworis</MenuItem>
                </Select>
        </FormControl>
    );
}