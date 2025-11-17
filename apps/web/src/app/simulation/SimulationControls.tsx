import React from "react";
import{Box, Slider, Typography, TextField} from "@mui/material";

type Props = {
    intensity: number;
    onIntensityChange: (v: number) => void;
    duration: number;
    onDurationChange: (v: number) => void;
};

export default function SimulationControls({intensity, onIntensityChange, duration, onDurationChange}: Props) {
    return (
    <Box sx={{display:'flex', flexDirection:'column', gap:2}}>
        <Box>
            <Typography variant="subtitle2" gutterBottom>
                Attack Intensity
            </Typography>
            <Slider
                value={intensity}
                onChange={(_, v) => onIntensityChange(v as number)}
                min={0}
                max={100}
                valueLabelDisplay="auto"
                />
        </Box>

        <Box sx={{display: 'flex', gap: 2, alignItems:'center'}}>
            <Typography variant="subtitle2">Duration (steps)</Typography>
            <TextField
                type="number"
                size="small"
                inputProps={{min:1, max:100}}
                value={duration}
                onChange={(e)=>{
                    const n = Math.max(1, Math.min(100, Number(e.target.value || 1)));
                    onDurationChange(n);
                }}
                sx={{width:100}}
                />
        </Box>
    </Box>
    );
}