export type Status = 'green' | 'yellow' | 'red' | null;

export interface ChecklistItem {
    id: string;
    name: string;
}

export interface InspectionCategory {
    id: string;
    name: string;
    icon: any;
    items: ChecklistItem[];
}

export const CATEGORIES: InspectionCategory[] = [
    {
        id: 'engine',
        name: 'Engine',
        icon: 'engine',
        items: [
            { id: 'eng_1', name: 'Oil Level & Condition' },
            { id: 'eng_2', name: 'Coolant Level & Hoses' },
            { id: 'eng_3', name: 'Belts & Pulleys' },
        ]
    },
    {
        id: 'undercarriage',
        name: 'Undercarriage',
        icon: 'tractor',
        items: [
            { id: 'und_1', name: 'Track Tension & Wear' },
            { id: 'und_2', name: 'Rollers & Idlers' },
            { id: 'und_3', name: 'Sprocket Condition' },
        ]
    },
    {
        id: 'hydraulics',
        name: 'Hydraulics',
        icon: 'hydraulic-oil-level',
        items: [
            { id: 'hyd_1', name: 'Fluid Level' },
            { id: 'hyd_2', name: 'Cylinders & Rods' },
            { id: 'hyd_3', name: 'Hoses & Connections' },
        ]
    },
    {
        id: 'cab',
        name: 'Cab & Controls',
        icon: 'car-seat',
        items: [
            { id: 'cab_1', name: 'Seatbelt & Safety Features' },
            { id: 'cab_2', name: 'Gauges & Indicators' },
            { id: 'cab_3', name: 'Joystick Controls' },
        ]
    }
];
