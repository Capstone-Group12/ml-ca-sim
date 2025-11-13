import React from "react";
import {Box, Typography, Paper, Table, TableBody, TableCell, TableHead, TableRow, Tab} from "@mui/material";
import {Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Title, 
    Tooltip,
    Legend
} from "chart.js";

ChartJS.register(
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Title,
    Tooltip,
    Legend
);

type Props = {
    results: number[];
};

export default function SimulationResults({results}: Props){
    const labels = results.map((_, i) => `Step ${i + 1}`);
    const avg = results.length ? (results.reduce((a, b)=> a + b, 0) /results.length).toFixed(1) :"-";

    const data = {
        labels,
        datasets:[
            {
                label: "Detection/Impact",
                data: results,
                borderColor: "#1976d2",
                backgroundColor: "rgba(25, 118, 210, 0.2)",
                tension: 0.2,
                fill : true,
            },
        ],
    };

    return (
        <Box sx={{mt:3}}>
            <Typography variant="h6" gutterBottom>
                Simulation Results
            </Typography>

            <Paper sx={{p:2, mb:2}}>
                <Line data={data} />
            </Paper>

            <Paper sx={{p:2}}>
                <Typography variant="subtitle2">Summary</Typography>
                <Typography variant="body2">Average:{avg}</Typography>

                <Table size="small" sx={{mt:1}}>
                    <TableHead>
                        <TableRow>
                            <TableCell>Step</TableCell>
                            <TableCell>Value</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {results.map((r, i) => (
                            <TableRow key={i}>
                                <TableCell>{i+1}</TableCell>
                                <TableCell>{r}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </Paper>
        </Box>
    )
};