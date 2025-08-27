// Brand Management JavaScript
let COLOR_VARIABLES = [];

// Professional Color Palettes
const FIXED_PRESETS = {
  'Current': {
    '--background': '51 100% 95% / 1',
    '--foreground': '220 80% 20% / 1',
    '--card': '0 0% 100% / 1',
    '--card-foreground': '220 80% 20% / 1',
    '--popover': '0 0% 100% / 1',
    '--popover-foreground': '220 80% 20% / 1',
    '--primary': '200 100% 50% / 1',
    '--primary-foreground': '0 0% 100% / 1',
    '--secondary': '340 100% 70% / 1',
    '--secondary-foreground': '220 80% 20% / 1',
    '--muted': '120 60% 90% / 1',
    '--muted-foreground': '220 80% 20% / 1',
    '--accent': '40 100% 60% / 1',
    '--accent-foreground': '220 80% 20% / 1',
    '--destructive': '0 72% 51% / 1',
    '--destructive-foreground': '0 0% 100% / 1',
    '--border': '220 13% 91% / 1',
    '--input': '0 0% 100% / 1',
    '--ring': '200 100% 50% / 1'
  },
  'Original': {
    '--background': '220 20% 99% / 1',
    '--foreground': '220 10% 15% / 1',
    '--card': '0 0% 100% / 1',
    '--card-foreground': '220 10% 15% / 1',
    '--popover': '0 0% 100% / 1',
    '--popover-foreground': '220 10% 15% / 1',
    '--primary': '358 50% 39% / 1',
    '--primary-foreground': '0 0% 100% / 1',
    '--secondary': '220 14% 96% / 1',
    '--secondary-foreground': '220 9% 31% / 1',
    '--muted': '220 14% 96% / 1',
    '--muted-foreground': '220 9% 46% / 1',
    '--accent': '220 14% 96% / 1',
    '--accent-foreground': '220 10% 15% / 1',
    '--destructive': '0 72% 51% / 1',
    '--destructive-foreground': '0 0% 100% / 1',
    '--border': '220 13% 91% / 1',
    '--input': '0 0% 100% / 1',
    '--ring': '358 50% 39% / 1'
  },
  'Light': {
    '--background': '0 0% 100% / 1',
    '--foreground': '222 84% 4.9% / 1',
    '--card': '0 0% 100% / 1',
    '--card-foreground': '222 84% 4.9% / 1',
    '--popover': '0 0% 100% / 1',
    '--popover-foreground': '222 84% 4.9% / 1',
    '--primary': '222 84% 4.9% / 1',
    '--primary-foreground': '210 40% 98% / 1',
    '--secondary': '210 40% 96% / 1',
    '--secondary-foreground': '222 84% 4.9% / 1',
    '--muted': '210 40% 96% / 1',
    '--muted-foreground': '215 16% 47% / 1',
    '--accent': '210 40% 96% / 1',
    '--accent-foreground': '222 84% 4.9% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '210 40% 98% / 1',
    '--border': '214 32% 91% / 1',
    '--input': '214 32% 91% / 1',
    '--ring': '222 84% 4.9% / 1'
  },
  'Dark': {
    '--background': '222 84% 4.9% / 1',
    '--foreground': '210 40% 98% / 1',
    '--card': '222 84% 4.9% / 1',
    '--card-foreground': '210 40% 98% / 1',
    '--popover': '222 84% 4.9% / 1',
    '--popover-foreground': '210 40% 98% / 1',
    '--primary': '210 40% 98% / 1',
    '--primary-foreground': '222 84% 4.9% / 1',
    '--secondary': '217 33% 17% / 1',
    '--secondary-foreground': '210 40% 98% / 1',
    '--muted': '217 33% 17% / 1',
    '--muted-foreground': '215 20% 65% / 1',
    '--accent': '217 33% 17% / 1',
    '--accent-foreground': '210 40% 98% / 1',
    '--destructive': '0 63% 31% / 1',
    '--destructive-foreground': '210 40% 98% / 1',
    '--border': '217 33% 17% / 1',
    '--input': '217 33% 17% / 1',
    '--ring': '212 100% 50% / 1'
  },
  'Capuchin': {
    '--background': '45 100% 98% / 1',
    '--foreground': '25 30% 15% / 1',
    '--card': '45 100% 99% / 1',
    '--card-foreground': '25 30% 15% / 1',
    '--popover': '45 100% 99% / 1',
    '--popover-foreground': '25 30% 15% / 1',
    '--primary': '25 95% 53% / 1',
    '--primary-foreground': '45 100% 98% / 1',
    '--secondary': '35 100% 85% / 1',
    '--secondary-foreground': '25 30% 15% / 1',
    '--muted': '45 50% 92% / 1',
    '--muted-foreground': '25 30% 35% / 1',
    '--accent': '15 100% 70% / 1',
    '--accent-foreground': '25 30% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '45 100% 98% / 1',
    '--border': '45 50% 88% / 1',
    '--input': '45 100% 99% / 1',
    '--ring': '25 95% 53% / 1'
  },
  'Golden Orange': {
    '--background': '35 100% 97% / 1',
    '--foreground': '35 40% 15% / 1',
    '--card': '35 100% 99% / 1',
    '--card-foreground': '35 40% 15% / 1',
    '--popover': '35 100% 99% / 1',
    '--popover-foreground': '35 40% 15% / 1',
    '--primary': '35 100% 50% / 1',
    '--primary-foreground': '35 100% 97% / 1',
    '--secondary': '25 100% 80% / 1',
    '--secondary-foreground': '35 40% 15% / 1',
    '--muted': '35 50% 90% / 1',
    '--muted-foreground': '35 40% 35% / 1',
    '--accent': '45 100% 65% / 1',
    '--accent-foreground': '35 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '35 100% 97% / 1',
    '--border': '35 50% 85% / 1',
    '--input': '35 100% 99% / 1',
    '--ring': '35 100% 50% / 1'
  },
  'Ocean': {
    '--background': '190 50% 98% / 1',
    '--foreground': '190 40% 15% / 1',
    '--card': '190 50% 99% / 1',
    '--card-foreground': '190 40% 15% / 1',
    '--popover': '190 50% 99% / 1',
    '--popover-foreground': '190 40% 15% / 1',
    '--primary': '190 100% 45% / 1',
    '--primary-foreground': '190 50% 98% / 1',
    '--secondary': '180 100% 80% / 1',
    '--secondary-foreground': '190 40% 15% / 1',
    '--muted': '190 30% 90% / 1',
    '--muted-foreground': '190 40% 35% / 1',
    '--accent': '170 100% 70% / 1',
    '--accent-foreground': '190 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '190 50% 98% / 1',
    '--border': '190 30% 85% / 1',
    '--input': '190 50% 99% / 1',
    '--ring': '190 100% 45% / 1'
  },
  'Forest': {
    '--background': '140 30% 98% / 1',
    '--foreground': '140 40% 15% / 1',
    '--card': '140 30% 99% / 1',
    '--card-foreground': '140 40% 15% / 1',
    '--popover': '140 30% 99% / 1',
    '--popover-foreground': '140 40% 15% / 1',
    '--primary': '140 100% 35% / 1',
    '--primary-foreground': '140 30% 98% / 1',
    '--secondary': '160 100% 80% / 1',
    '--secondary-foreground': '140 40% 15% / 1',
    '--muted': '140 20% 90% / 1',
    '--muted-foreground': '140 40% 35% / 1',
    '--accent': '120 100% 70% / 1',
    '--accent-foreground': '140 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '140 30% 98% / 1',
    '--border': '140 20% 85% / 1',
    '--input': '140 30% 99% / 1',
    '--ring': '140 100% 35% / 1'
  },
  'Sunset': {
    '--background': '10 100% 98% / 1',
    '--foreground': '10 40% 15% / 1',
    '--card': '10 100% 99% / 1',
    '--card-foreground': '10 40% 15% / 1',
    '--popover': '10 100% 99% / 1',
    '--popover-foreground': '10 40% 15% / 1',
    '--primary': '10 100% 55% / 1',
    '--primary-foreground': '10 100% 98% / 1',
    '--secondary': '25 100% 80% / 1',
    '--secondary-foreground': '10 40% 15% / 1',
    '--muted': '10 50% 90% / 1',
    '--muted-foreground': '10 40% 35% / 1',
    '--accent': '0 100% 70% / 1',
    '--accent-foreground': '10 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '10 100% 98% / 1',
    '--border': '10 50% 85% / 1',
    '--input': '10 100% 99% / 1',
    '--ring': '10 100% 55% / 1'
  },
  'Vibrant': {
    '--background': '280 100% 95% / 1',
    '--foreground': '280 80% 20% / 1',
    '--card': '0 0% 100% / 1',
    '--card-foreground': '280 80% 20% / 1',
    '--popover': '0 0% 100% / 1',
    '--popover-foreground': '280 80% 20% / 1',
    '--primary': '280 100% 60% / 1',
    '--primary-foreground': '0 0% 100% / 1',
    '--secondary': '320 100% 70% / 1',
    '--secondary-foreground': '280 80% 20% / 1',
    '--muted': '280 60% 90% / 1',
    '--muted-foreground': '280 80% 20% / 1',
    '--accent': '300 100% 60% / 1',
    '--accent-foreground': '280 80% 20% / 1',
    '--destructive': '0 72% 51% / 1',
    '--destructive-foreground': '0 0% 100% / 1',
    '--border': '280 13% 91% / 1',
    '--input': '0 0% 100% / 1',
    '--ring': '280 100% 60% / 1'
  },
  'Midnight': {
    '--background': '240 10% 8% / 1',
    '--foreground': '240 10% 95% / 1',
    '--card': '240 10% 12% / 1',
    '--card-foreground': '240 10% 95% / 1',
    '--popover': '240 10% 12% / 1',
    '--popover-foreground': '240 10% 95% / 1',
    '--primary': '240 100% 60% / 1',
    '--primary-foreground': '240 10% 8% / 1',
    '--secondary': '240 10% 20% / 1',
    '--secondary-foreground': '240 10% 95% / 1',
    '--muted': '240 10% 20% / 1',
    '--muted-foreground': '240 10% 70% / 1',
    '--accent': '240 10% 20% / 1',
    '--accent-foreground': '240 10% 95% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '240 10% 95% / 1',
    '--border': '240 10% 25% / 1',
    '--input': '240 10% 12% / 1',
    '--ring': '240 100% 60% / 1'
  },
  'Rose': {
    '--background': '350 100% 98% / 1',
    '--foreground': '350 40% 15% / 1',
    '--card': '350 100% 99% / 1',
    '--card-foreground': '350 40% 15% / 1',
    '--popover': '350 100% 99% / 1',
    '--popover-foreground': '350 40% 15% / 1',
    '--primary': '350 100% 55% / 1',
    '--primary-foreground': '350 100% 98% / 1',
    '--secondary': '340 100% 85% / 1',
    '--secondary-foreground': '350 40% 15% / 1',
    '--muted': '350 50% 92% / 1',
    '--muted-foreground': '350 40% 35% / 1',
    '--accent': '330 100% 70% / 1',
    '--accent-foreground': '350 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '350 100% 98% / 1',
    '--border': '350 50% 88% / 1',
    '--input': '350 100% 99% / 1',
    '--ring': '350 100% 55% / 1'
  },
  
  // Additional Classic Palettes
  'Neutral': {
    '--background': '0 0% 98% / 1',
    '--foreground': '0 0% 15% / 1',
    '--card': '0 0% 100% / 1',
    '--card-foreground': '0 0% 15% / 1',
    '--popover': '0 0% 100% / 1',
    '--popover-foreground': '0 0% 15% / 1',
    '--primary': '0 0% 25% / 1',
    '--primary-foreground': '0 0% 98% / 1',
    '--secondary': '0 0% 85% / 1',
    '--secondary-foreground': '0 0% 15% / 1',
    '--muted': '0 0% 92% / 1',
    '--muted-foreground': '0 0% 45% / 1',
    '--accent': '0 0% 80% / 1',
    '--accent-foreground': '0 0% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '0 0% 98% / 1',
    '--border': '0 0% 88% / 1',
    '--input': '0 0% 100% / 1',
    '--ring': '0 0% 25% / 1'
  },
  
  'Warm': {
    '--background': '50 50% 98% / 1',
    '--foreground': '50 40% 15% / 1',
    '--card': '50 50% 100% / 1',
    '--card-foreground': '50 40% 15% / 1',
    '--popover': '50 50% 100% / 1',
    '--popover-foreground': '50 40% 15% / 1',
    '--primary': '50 100% 45% / 1',
    '--primary-foreground': '50 50% 98% / 1',
    '--secondary': '60 100% 80% / 1',
    '--secondary-foreground': '50 40% 15% / 1',
    '--muted': '50 30% 92% / 1',
    '--muted-foreground': '50 40% 35% / 1',
    '--accent': '40 100% 70% / 1',
    '--accent-foreground': '50 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '50 50% 98% / 1',
    '--border': '50 30% 88% / 1',
    '--input': '50 50% 100% / 1',
    '--ring': '50 100% 45% / 1'
  },
  
  'Cool': {
    '--background': '240 50% 98% / 1',
    '--foreground': '240 40% 15% / 1',
    '--card': '240 50% 100% / 1',
    '--card-foreground': '240 40% 15% / 1',
    '--popover': '240 50% 100% / 1',
    '--popover-foreground': '240 40% 15% / 1',
    '--primary': '240 100% 45% / 1',
    '--primary-foreground': '240 50% 98% / 1',
    '--secondary': '250 100% 80% / 1',
    '--secondary-foreground': '240 40% 15% / 1',
    '--muted': '240 30% 92% / 1',
    '--muted-foreground': '240 40% 35% / 1',
    '--accent': '260 100% 70% / 1',
    '--accent-foreground': '240 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '240 50% 98% / 1',
    '--border': '240 30% 88% / 1',
    '--input': '240 50% 100% / 1',
    '--ring': '240 100% 45% / 1'
  },
  
  'Elegant': {
    '--background': '320 30% 98% / 1',
    '--foreground': '320 40% 15% / 1',
    '--card': '320 30% 100% / 1',
    '--card-foreground': '320 40% 15% / 1',
    '--popover': '320 30% 100% / 1',
    '--popover-foreground': '320 40% 15% / 1',
    '--primary': '320 100% 45% / 1',
    '--primary-foreground': '320 30% 98% / 1',
    '--secondary': '340 100% 80% / 1',
    '--secondary-foreground': '320 40% 15% / 1',
    '--muted': '320 20% 92% / 1',
    '--muted-foreground': '320 40% 35% / 1',
    '--accent': '340 100% 70% / 1',
    '--accent-foreground': '320 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '320 30% 98% / 1',
    '--border': '320 20% 88% / 1',
    '--input': '320 30% 100% / 1',
    '--ring': '320 100% 45% / 1'
  },
  
  'Aurora': {
    '--background': '160 50% 98% / 1',
    '--foreground': '160 40% 15% / 1',
    '--card': '160 50% 100% / 1',
    '--card-foreground': '160 40% 15% / 1',
    '--popover': '160 50% 100% / 1',
    '--popover-foreground': '160 40% 15% / 1',
    '--primary': '160 100% 45% / 1',
    '--primary-foreground': '160 50% 98% / 1',
    '--secondary': '180 100% 80% / 1',
    '--secondary-foreground': '160 40% 15% / 1',
    '--muted': '160 30% 92% / 1',
    '--muted-foreground': '160 40% 35% / 1',
    '--accent': '140 100% 70% / 1',
    '--accent-foreground': '160 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '160 50% 98% / 1',
    '--border': '160 30% 88% / 1',
    '--input': '160 50% 100% / 1',
    '--ring': '160 100% 45% / 1'
  },
  
  'Coral': {
    '--background': '15 50% 98% / 1',
    '--foreground': '15 40% 15% / 1',
    '--card': '15 50% 100% / 1',
    '--card-foreground': '15 40% 15% / 1',
    '--popover': '15 50% 100% / 1',
    '--popover-foreground': '15 40% 15% / 1',
    '--primary': '15 100% 45% / 1',
    '--primary-foreground': '15 50% 98% / 1',
    '--secondary': '25 100% 80% / 1',
    '--secondary-foreground': '15 40% 15% / 1',
    '--muted': '15 30% 92% / 1',
    '--muted-foreground': '15 40% 35% / 1',
    '--accent': '5 100% 70% / 1',
    '--accent-foreground': '15 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '15 50% 98% / 1',
    '--border': '15 30% 88% / 1',
    '--input': '15 50% 100% / 1',
    '--ring': '15 100% 45% / 1'
  },
  'Capuchin Blue': {
    '--background': '220 50% 98% / 1',
    '--foreground': '220 40% 15% / 1',
    '--card': '220 50% 99% / 1',
    '--card-foreground': '220 40% 15% / 1',
    '--popover': '220 50% 99% / 1',
    '--popover-foreground': '220 40% 15% / 1',
    '--primary': '220 100% 45% / 1',
    '--primary-foreground': '220 50% 98% / 1',
    '--secondary': '230 100% 80% / 1',
    '--secondary-foreground': '220 40% 15% / 1',
    '--muted': '220 30% 90% / 1',
    '--muted-foreground': '220 40% 35% / 1',
    '--accent': '240 100% 70% / 1',
    '--accent-foreground': '220 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '220 50% 98% / 1',
    '--border': '220 30% 85% / 1',
    '--input': '220 50% 99% / 1',
    '--ring': '220 100% 45% / 1'
  },
  'Capuchin Green': {
    '--background': '100 30% 98% / 1',
    '--foreground': '100 40% 15% / 1',
    '--card': '100 30% 99% / 1',
    '--card-foreground': '100 40% 15% / 1',
    '--popover': '100 30% 99% / 1',
    '--popover-foreground': '100 40% 15% / 1',
    '--primary': '100 100% 35% / 1',
    '--primary-foreground': '100 30% 98% / 1',
    '--secondary': '120 100% 80% / 1',
    '--secondary-foreground': '100 40% 15% / 1',
    '--muted': '100 20% 90% / 1',
    '--muted-foreground': '100 40% 35% / 1',
    '--accent': '80 100% 70% / 1',
    '--accent-foreground': '100 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '100 30% 98% / 1',
    '--border': '100 20% 85% / 1',
    '--input': '100 30% 99% / 1',
    '--ring': '100 100% 35% / 1'
  },
  'Capuchin Dark': {
    '--background': '25 30% 8% / 1',
    '--foreground': '45 100% 95% / 1',
    '--card': '25 30% 12% / 1',
    '--card-foreground': '45 100% 95% / 1',
    '--popover': '25 30% 12% / 1',
    '--popover-foreground': '45 100% 95% / 1',
    '--primary': '25 95% 53% / 1',
    '--primary-foreground': '25 30% 8% / 1',
    '--secondary': '35 100% 20% / 1',
    '--secondary-foreground': '45 100% 95% / 1',
    '--muted': '25 30% 20% / 1',
    '--muted-foreground': '45 50% 70% / 1',
    '--accent': '15 100% 40% / 1',
    '--accent-foreground': '45 100% 95% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '45 100% 95% / 1',
    '--border': '25 30% 25% / 1',
    '--input': '25 30% 12% / 1',
    '--ring': '25 95% 53% / 1'
  },
  'Capuchin Blue Dark': {
    '--background': '210 40% 8% / 1',
    '--foreground': '210 50% 95% / 1',
    '--card': '210 40% 12% / 1',
    '--card-foreground': '210 50% 95% / 1',
    '--popover': '210 40% 12% / 1',
    '--popover-foreground': '210 50% 95% / 1',
    '--primary': '210 100% 45% / 1',
    '--primary-foreground': '210 40% 8% / 1',
    '--secondary': '200 100% 20% / 1',
    '--secondary-foreground': '210 50% 95% / 1',
    '--muted': '210 30% 20% / 1',
    '--muted-foreground': '210 50% 70% / 1',
    '--accent': '220 100% 40% / 1',
    '--accent-foreground': '210 50% 95% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '210 50% 95% / 1',
    '--border': '210 30% 25% / 1',
    '--input': '210 40% 12% / 1',
    '--ring': '210 100% 45% / 1'
  },
  'Capuchin Green Dark': {
    '--background': '120 30% 8% / 1',
    '--foreground': '120 40% 95% / 1',
    '--card': '120 30% 12% / 1',
    '--card-foreground': '120 40% 95% / 1',
    '--popover': '120 30% 12% / 1',
    '--popover-foreground': '120 40% 95% / 1',
    '--primary': '120 100% 35% / 1',
    '--primary-foreground': '120 30% 8% / 1',
    '--secondary': '140 100% 20% / 1',
    '--secondary-foreground': '120 40% 95% / 1',
    '--muted': '120 20% 20% / 1',
    '--muted-foreground': '120 40% 70% / 1',
    '--accent': '100 100% 40% / 1',
    '--accent-foreground': '120 40% 95% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '120 40% 95% / 1',
    '--border': '120 20% 25% / 1',
    '--input': '120 30% 12% / 1',
    '--ring': '120 100% 35% / 1'
  },
  
  'Capuchin Purple': {
    '--background': '270 30% 98% / 1',
    '--foreground': '270 40% 15% / 1',
    '--card': '270 30% 99% / 1',
    '--card-foreground': '270 40% 15% / 1',
    '--popover': '270 30% 99% / 1',
    '--popover-foreground': '270 40% 15% / 1',
    '--primary': '270 100% 35% / 1',
    '--primary-foreground': '270 30% 98% / 1',
    '--secondary': '280 100% 80% / 1',
    '--secondary-foreground': '270 40% 15% / 1',
    '--muted': '270 20% 90% / 1',
    '--muted-foreground': '270 40% 35% / 1',
    '--accent': '260 100% 70% / 1',
    '--accent-foreground': '270 40% 15% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '270 30% 98% / 1',
    '--border': '270 20% 85% / 1',
    '--input': '270 30% 99% / 1',
    '--ring': '270 100% 35% / 1'
  },
  
  'Capuchin Purple Dark': {
    '--background': '270 40% 8% / 1',
    '--foreground': '270 30% 95% / 1',
    '--card': '270 40% 12% / 1',
    '--card-foreground': '270 30% 95% / 1',
    '--popover': '270 40% 12% / 1',
    '--popover-foreground': '270 30% 95% / 1',
    '--primary': '270 100% 35% / 1',
    '--primary-foreground': '270 40% 8% / 1',
    '--secondary': '280 100% 20% / 1',
    '--secondary-foreground': '270 30% 95% / 1',
    '--muted': '270 30% 15% / 1',
    '--muted-foreground': '270 30% 65% / 1',
    '--accent': '260 100% 40% / 1',
    '--accent-foreground': '270 30% 95% / 1',
    '--destructive': '0 84% 60% / 1',
    '--destructive-foreground': '270 40% 8% / 1',
    '--border': '270 30% 20% / 1',
    '--input': '270 40% 12% / 1',
    '--ring': '270 100% 35% / 1'
  }
};

// Utility functions
function getCSRFToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }
  // If CSRF protection is disabled, return null
  return null;
}

function hslString(hsl) {
  return `hsl(${hsl})`;
}

function refreshBrandImages() {
  document.getElementById('brand-logo-header').src = '/static/pic/logo.png?' + Date.now();
  document.getElementById('brand-logo-footer').src = '/static/pic/logo_footer.png?' + Date.now();
  document.getElementById('brand-favicon').src = '/static/pic/favicon.png?' + Date.now();
  document.getElementById('brand-placeholder').src = '/static/pic/placeholder.png?' + Date.now();
}

// Utility functions for color conversion
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16)
  ] : null;
}

function rgbToHsl(r, g, b) {
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;

  if (max === min) {
    h = s = 0; // achromatic
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }

  return [h * 360, s * 100, l * 100];
}

function hslToHex(h, s, l) {
  s /= 100;
  l /= 100;

  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((h / 60) % 2 - 1));
  const m = l - c / 2;
  let r = 0, g = 0, b = 0;

  if (0 <= h && h < 60) {
    r = c; g = x; b = 0;
  } else if (60 <= h && h < 120) {
    r = x; g = c; b = 0;
  } else if (120 <= h && h < 180) {
    r = 0; g = c; b = x;
  } else if (180 <= h && h < 240) {
    r = 0; g = x; b = c;
  } else if (240 <= h && h < 300) {
    r = x; g = 0; b = c;
  } else if (300 <= h && h < 360) {
    r = c; g = 0; b = x;
  }

  const rHex = Math.round((r + m) * 255).toString(16).padStart(2, '0');
  const gHex = Math.round((g + m) * 255).toString(16).padStart(2, '0');
  const bHex = Math.round((b + m) * 255).toString(16).padStart(2, '0');

  return `#${rHex}${gHex}${bHex}`;
}

// Color palette functions
function renderColorPaletteTable() {
  const tbody = document.getElementById('color-palette-table');
  if (!tbody) return;

  tbody.innerHTML = COLOR_VARIABLES.map((cv, idx) => {
    const hslMatch = cv.value.match(/^(\d+)\s+(\d+)%\s+(\d+)%\s*\/\s*([\d.]+)$/);
    if (!hslMatch) return '';

    const [, h, s, l, a] = hslMatch;
    const hex = hslToHex(parseInt(h), parseInt(s), parseInt(l));
    const alpha = parseFloat(a);

    return `
      <tr class="hover:bg-gray-50 transition-colors">
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-lg border-2 border-gray-300 shadow-sm" style="background-color: ${hex};"></div>
            <span class="text-sm font-medium text-gray-900">${cv.name.replace('--', '')}</span>
          </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="text-sm text-gray-600 font-mono">${cv.name}</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="text-sm text-gray-600 font-mono">${cv.value}</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <button onclick="showColorPicker(${idx})" class="w-8 h-8 flex items-center justify-center bg-blue-100 hover:bg-blue-200 text-blue-600 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors" aria-label="Edit warna ${cv.name}" title="Edit Warna">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.792-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.5M6 18l-2.685.792a4.5 4.5 0 01-1.897-1.13L6 18z" />
            </svg>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// Modal functions
function openColorPickerModal() {
  const modal = document.getElementById('color-picker-modal');
  if (modal) {
    modal.classList.remove('hidden');
    setTimeout(() => modal.style.opacity = '1', 10);
  }
}

function closeColorPickerModal() {
  const modal = document.getElementById('color-picker-modal');
  if (modal) {
    modal.style.opacity = '0';
    setTimeout(() => modal.classList.add('hidden'), 300);
  }
}

function closeColorPickerModalOnClickOutside(event) {
  if (event.target.id === 'color-picker-modal') {
    closeColorPickerModal();
  }
}

let currentEditingIndex = -1;
let currentEditingVariable = '';

function showColorPicker(idx) {
  currentEditingIndex = idx;
  const cv = COLOR_VARIABLES[idx];
  if (!cv) return;

  currentEditingVariable = cv.name;
  const hslMatch = cv.value.match(/^(\d+)\s+(\d+)%\s+(\d+)%\s*\/\s*([\d.]+)$/);
  if (!hslMatch) return;

  const [, h, s, l, a] = hslMatch;
  const hex = hslToHex(parseInt(h), parseInt(s), parseInt(l));
  const alpha = parseFloat(a);

  const content = document.getElementById('color-picker-content');
  if (content) {
    content.innerHTML = `
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Warna</label>
          <input type="color" id="color-picker" value="${hex}" class="w-full h-12 rounded-lg border border-gray-300 cursor-pointer">
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Transparansi: <span id="alpha-value">${Math.round(alpha * 100)}%</span></label>
          <input type="range" id="alpha-slider" min="0" max="100" value="${Math.round(alpha * 100)}" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider">
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
          <p class="text-sm text-gray-600">Preview: <span id="color-preview" class="font-mono">${cv.value}</span></p>
        </div>
      </div>
    `;

    // Add event listeners
    const colorInput = document.getElementById('color-picker');
    const alphaSlider = document.getElementById('alpha-slider');
    const alphaValue = document.getElementById('alpha-value');
    const colorPreview = document.getElementById('color-preview');

    function updatePreview() {
      const hex = colorInput.value;
      const alpha = alphaSlider.value / 100;
      const rgb = hexToRgb(hex);
      if (rgb) {
        const [h, s, l] = rgbToHsl(rgb[0], rgb[1], rgb[2]);
        const newValue = `${Math.round(h)} ${Math.round(s)}% ${Math.round(l)}% / ${alpha}`;
        colorPreview.textContent = newValue;
        colorPreview.style.color = hex;
      }
      alphaValue.textContent = `${alphaSlider.value}%`;
    }

    colorInput.addEventListener('input', updatePreview);
    alphaSlider.addEventListener('input', updatePreview);
    updatePreview();

    // Confirm button handler
    const confirmBtn = document.getElementById('confirm-color-btn');
    if (confirmBtn) {
      confirmBtn.onclick = function() {
        const hex = colorInput.value;
        const alpha = alphaSlider.value / 100;
        const rgb = hexToRgb(hex);
        if (rgb) {
          const [h, s, l] = rgbToHsl(rgb[0], rgb[1], rgb[2]);
          const newValue = `${Math.round(h)} ${Math.round(s)}% ${Math.round(l)}% / ${alpha}`;
          updateColorVariable(cv.name, newValue);
          closeColorPickerModal();
        }
      };
    }

    // Cancel button handler
    const cancelBtn = document.getElementById('cancel-color-btn');
    if (cancelBtn) {
      cancelBtn.onclick = closeColorPickerModal;
    }
  }

  openColorPickerModal();
}

async function updateColorVariable(variable, value) {
  try {
    const headers = {
      'Content-Type': 'application/json'
    };
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
    
    const response = await fetch('/api/brand-colors', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ variable, value })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    // Update local COLOR_VARIABLES
    const cv = COLOR_VARIABLES.find(cv => cv.name === variable);
    if (cv) {
      cv.value = value;
    }

    // Re-render table
    renderColorPaletteTable();
    
    // Reload CSS
    const link = document.querySelector('link[href*="base_css.css"]');
    if (link) {
      link.href = link.href.split('?')[0] + '?v=' + Date.now();
    }

    showToast('success', 'Warna berhasil diperbarui!');
  } catch (err) {
    console.error('Error updating color:', err);
    showToast('error', 'Gagal memperbarui warna: ' + err.message);
  }
}

// Preset management
function getCustomPresets() {
  const stored = localStorage.getItem('customColorPresets');
  return stored ? JSON.parse(stored) : {};
}

function saveCustomPreset(name, palette) {
  const custom = getCustomPresets();
  custom[name] = palette;
  localStorage.setItem('customColorPresets', JSON.stringify(custom));
}

// Categorize presets
const PRESET_CATEGORIES = {
  classic: ['Current', 'Original', 'Light', 'Dark', 'Neutral', 'Warm', 'Cool', 'Elegant'],
  capuchin: ['Capuchin', 'Capuchin Dark', 'Capuchin Blue', 'Capuchin Blue Dark', 'Capuchin Green', 'Capuchin Green Dark', 'Capuchin Purple', 'Capuchin Purple Dark'],
  themed: ['Ocean', 'Forest', 'Sunset', 'Vibrant', 'Midnight', 'Rose', 'Aurora', 'Coral']
};

function createPaletteCard(name, palette) {
  const card = document.createElement('div');
  card.className = 'bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 border border-gray-200 overflow-hidden palette-card';
  card.setAttribute('data-palette-name', name);
  
  // Create color preview squares
  const colorSquares = Object.entries(palette).slice(0, 8).map(([key, value]) => {
    const hslMatch = value.match(/^(\d+)\s+(\d+)%\s+(\d+)%\s*\/\s*([\d.]+)$/);
    if (!hslMatch) return '';
    
    const [, h, s, l, a] = hslMatch;
    const hex = hslToHex(parseInt(h), parseInt(s), parseInt(l));
    
    // Determine border color based on lightness
    const lightness = parseInt(l);
    const borderColor = lightness > 70 ? '#d1d5db' : lightness > 40 ? '#9ca3af' : '#374151';
    
    return `<div class="w-8 h-8 rounded-lg color-square shadow-sm" style="background: linear-gradient(135deg, ${hex} 0%, ${hex} 100%); border: 2px solid ${borderColor};" title="${key}"></div>`;
  }).join('');
  
  card.innerHTML = `
    <div class="p-4">
      <div class="flex items-center justify-between mb-3">
        <h4 class="font-semibold text-gray-800 text-sm">${name}</h4>
        <button class="apply-palette-btn bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white px-3 py-1 rounded text-xs font-medium transition-all duration-300 shadow-sm flex items-center gap-1" data-palette="${name}">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 7.5h-.75A2.25 2.25 0 004.5 9.75v7.5a2.25 2.25 0 002.25 2.25h7.5a2.25 2.25 0 002.25-2.25v-7.5a2.25 2.25 0 00-2.25-2.25h-.75m-6 3l-3-3m0 0l-3 3m3-3v11.25m6-5.25h-.75a2.25 2.25 0 00-2.25 2.25v7.5a2.25 2.25 0 002.25 2.25h7.5a2.25 2.25 0 002.25-2.25v-7.5a2.25 2.25 0 00-2.25-2.25h-.75" />
          </svg>
          Apply
        </button>
      </div>
      <div class="grid grid-cols-4 gap-2 mb-3">
        ${colorSquares}
      </div>
      <div class="text-xs text-gray-500">
        ${Object.keys(palette).length} colors
      </div>
    </div>
  `;
  
  return card;
}

function populatePaletteTabs() {
  // Populate Classic tab
  const classicContainer = document.querySelector('#classic-palettes .grid');
  if (classicContainer) {
    classicContainer.innerHTML = '';
    PRESET_CATEGORIES.classic.forEach(name => {
      const palette = FIXED_PRESETS[name];
      if (palette) {
        classicContainer.appendChild(createPaletteCard(name, palette));
      }
    });
  }
  
  // Populate Capuchin tab
  const capuchinContainer = document.querySelector('#capuchin-palettes .grid');
  if (capuchinContainer) {
    capuchinContainer.innerHTML = '';
    PRESET_CATEGORIES.capuchin.forEach(name => {
      const palette = FIXED_PRESETS[name];
      if (palette) {
        capuchinContainer.appendChild(createPaletteCard(name, palette));
      }
    });
  }
  
  // Populate Themed tab
  const themedContainer = document.querySelector('#themed-palettes .grid');
  if (themedContainer) {
    themedContainer.innerHTML = '';
    PRESET_CATEGORIES.themed.forEach(name => {
      const palette = FIXED_PRESETS[name];
      if (palette) {
        themedContainer.appendChild(createPaletteCard(name, palette));
      }
    });
  }
}

function getPresetPalette(name) {
  if (name.startsWith('__custom__')) {
    const custom = getCustomPresets();
    return custom[name.replace('__custom__', '')];
  }
  return FIXED_PRESETS[name] || null;
}

function previewPreset(name) {
  const palette = getPresetPalette(name);
  if (!palette) return;
  
  // Update COLOR_VARIABLES in-place for preview only
  COLOR_VARIABLES.forEach(cv => {
    if (palette[cv.name]) {
      cv.value = palette[cv.name];
    }
  });
  renderColorPaletteTable();
}

// Form handling
function handleBrandForm(formId, fieldName) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    const fileInput = form.querySelector('input[type="file"]');
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (!fileInput.files.length) {
      showToast('warning', 'Pilih file terlebih dahulu!');
      return;
    }
    
    // Get file info for user feedback
    const file = fileInput.files[0];
    const originalSize = file.size;
    const originalName = file.name;
    
    // Show processing state
    const originalButtonText = submitButton.innerHTML;
    submitButton.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 animate-spin">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
      </svg>
      Memproses...
    `;
    submitButton.disabled = true;
    
    formData.append(fieldName, file);
    
    try {
      const headers = {};
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      const resp = await fetch('/api/brand-identity', {
        method: 'POST',
        headers: headers,
        body: formData
      });
      
      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({}));
        throw new Error(errorData.error || 'Upload failed');
      }
      
      // Get optimized file size info
      const result = await resp.json();
      
      // Show success message with optimization info
      const assetType = getAssetTypeName(fieldName);
      showToast('success', `${assetType} berhasil dioptimasi dan diunggah!`);
      
      refreshBrandImages();
      form.reset();
      
    } catch (err) {
      console.error('Upload error:', err);
      showToast('error', 'Gagal mengunggah gambar: ' + err.message);
    } finally {
      // Restore button state
      submitButton.innerHTML = originalButtonText;
      submitButton.disabled = false;
    }
  });
}

// Helper function to get user-friendly asset type names
function getAssetTypeName(fieldName) {
  const assetNames = {
    'logo_header': 'Logo Header',
    'logo_footer': 'Logo Footer', 
    'favicon': 'Favicon',
    'placeholder_image': 'Gambar Placeholder'
  };
  return assetNames[fieldName] || 'Gambar';
}

function handleBrandTextForm(formId, fieldName) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const input = form.querySelector('input[type="text"]');
    const value = input.value.trim();
    
    if (!value) {
      showToast('warning', 'Field tidak boleh kosong!');
      return;
    }
    
    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      const resp = await fetch('/api/brand-identity/text', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          field: fieldName,
          value: value
        })
      });
      
      if (!resp.ok) throw new Error('Update failed');
      
      showToast('success', `${fieldName === 'brand_name' ? 'Brand name' : 'Tagline'} berhasil diperbarui!`);
      
      // Update the input value to reflect the saved state
      input.value = value;
      
    } catch (err) {
      console.error('Update error:', err);
      showToast('error', `Gagal memperbarui ${fieldName === 'brand_name' ? 'brand name' : 'tagline'}: ` + err.message);
    }
  });
}

// Homepage Design Management
function handleHomepageDesignForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  // Remove any existing event listeners to prevent duplicates
  const newForm = form.cloneNode(true);
  form.parentNode.replaceChild(newForm, form);
  
  newForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Disable the button to prevent multiple submissions
    const submitBtn = newForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Updating...
    `;
    
    const formData = new FormData(newForm);
    const designType = formData.get('homepage_design');
    
    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      const resp = await fetch('/api/brand-identity/text', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          field: 'homepage_design',
          value: designType
        })
      });
      
      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${resp.status}: ${resp.statusText}`);
      }
      
      showToast('success', 'Homepage design updated successfully!');
      
      // Update all button states
      document.querySelectorAll('[name="homepage_design"]').forEach(btn => {
        const parentForm = btn.closest('form');
        const isActive = parentForm.id === formId;
        btn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          ${isActive ? 'Active' : 'Set as Active'}
        `;
      });
      
    } catch (err) {
      console.error('Update error:', err);
      showToast('error', 'Failed to update homepage design: ' + err.message);
    } finally {
      // Re-enable the button
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

// Categories Display Location Management
function handleCategoriesDisplayForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  // Remove any existing event listeners to prevent duplicates
  const newForm = form.cloneNode(true);
  form.parentNode.replaceChild(newForm, form);
  
  newForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Disable the button to prevent multiple submissions
    const submitBtn = newForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Updating...
    `;
    
    const formData = new FormData(newForm);
    const displayLocation = formData.get('categories_display_location');
    
    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      const resp = await fetch('/api/brand-identity/text', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          field: 'categories_display_location',
          value: displayLocation
        })
      });
      
      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${resp.status}: ${resp.statusText}`);
      }
      
      showToast('success', 'Categories display location updated successfully!');
      
      // Update all button states
      document.querySelectorAll('[name="categories_display_location"]').forEach(btn => {
        const parentForm = btn.closest('form');
        const isActive = parentForm.id === formId;
        btn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          ${isActive ? 'Active' : 'Set as Active'}
        `;
      });
      
    } catch (err) {
      console.error('Update error:', err);
      showToast('error', 'Failed to update categories display location: ' + err.message);
    } finally {
      // Re-enable the button
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

// Card Design Management
function handleCardDesignForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  // Remove any existing event listeners to prevent duplicates
  const newForm = form.cloneNode(true);
  form.parentNode.replaceChild(newForm, form);
  
  newForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Disable the button to prevent multiple submissions
    const submitBtn = newForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Updating...
    `;
    
    const formData = new FormData(newForm);
    const cardDesign = formData.get('card_design');
    
    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      const resp = await fetch('/api/brand-identity/text', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          field: 'card_design',
          value: cardDesign
        })
      });
      
      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${resp.status}: ${resp.statusText}`);
      }
      
      showToast('success', 'Card design updated successfully!');
      
      // Update all button states
      document.querySelectorAll('[name="card_design"]').forEach(btn => {
        const parentForm = btn.closest('form');
        const isActive = parentForm.id === formId;
        btn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          ${isActive ? 'Active' : 'Set as Active'}
        `;
      });
      
      // Update brand info in all open pages
      if (window.brandInfo) {
        window.brandInfo.card_design = cardDesign;
      }
      
      // Trigger card design refresh on news page if it's open
      if (window.refreshNewsCards) {
        window.refreshNewsCards();
      }
      
      // Dispatch custom event for other pages to listen to
      window.dispatchEvent(new CustomEvent('cardDesignChanged', { 
        detail: { cardDesign: cardDesign } 
      }));
      
    } catch (err) {
      console.error('Update error:', err);
      showToast('error', 'Failed to update card design: ' + err.message);
    } finally {
      // Re-enable the button
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

// Debug function for card design issues
function debugCardDesign(formId) {
  console.log('🔍 Debugging card design form:', formId);
  const form = document.getElementById(formId);
  if (!form) {
    console.error('❌ Form not found:', formId);
    return;
  }
  
  const submitBtn = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  const cardDesign = formData.get('card_design');
  
  console.log('📋 Form data:', {
    formId: formId,
    cardDesign: cardDesign,
    submitBtn: submitBtn ? 'Found' : 'Not found',
    submitBtnDisabled: submitBtn ? submitBtn.disabled : 'N/A'
  });
}

// Initialize everything
document.addEventListener('DOMContentLoaded', function() {
  // Load color palette
  fetch('/api/brand-colors')
    .then(resp => resp.json())
    .then(data => {
      COLOR_VARIABLES = data;
      populatePaletteTabs();
      renderColorPaletteTable();
    })
    .catch(err => console.error('Failed to load colors:', err));
  
  // Brand form handlers
  handleBrandForm('form-logo-header', 'logo_header');
  handleBrandForm('form-logo-footer', 'logo_footer');
  handleBrandForm('form-favicon', 'favicon');
  handleBrandForm('form-placeholder', 'placeholder_image');
  
  // Brand text form handlers
  handleBrandTextForm('form-brand-name', 'brand_name');
  handleBrandTextForm('form-tagline', 'tagline');
  
  // Homepage design form handlers
  handleHomepageDesignForm('form-homepage-news');
  handleHomepageDesignForm('form-homepage-albums');
  
  // Categories display location form handlers
  handleCategoriesDisplayForm('form-categories-body');
  handleCategoriesDisplayForm('form-categories-navbar');
  
  // Card design form handlers
  handleCardDesignForm('form-card-classic');
  handleCardDesignForm('form-card-modern');
  handleCardDesignForm('form-card-minimal');
  handleCardDesignForm('form-card-featured');
  
  // Tab switching functionality
  const paletteTabs = document.querySelectorAll('.palette-tab');
  paletteTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      const targetTab = this.getAttribute('data-tab');
      
      // Update tab states
      paletteTabs.forEach(t => {
        // Remove all possible gradient classes
        t.classList.remove('active', 'bg-gradient-to-r', 'from-amber-500', 'to-yellow-500', 'from-blue-500', 'to-indigo-500', 'from-gray-400', 'to-gray-500');
        // Add gray gradient for inactive
        t.classList.add('bg-gradient-to-r', 'from-gray-400', 'to-gray-500');
        t.setAttribute('aria-selected', 'false');
      });
      
      // Add amber gradient for active tab
      this.classList.add('active', 'bg-gradient-to-r', 'from-amber-500', 'to-yellow-500');
      this.classList.remove('bg-gradient-to-r', 'from-gray-400', 'to-gray-500', 'from-blue-500', 'to-indigo-500');
      this.setAttribute('aria-selected', 'true');
      
      // Show/hide content
      const allContents = document.querySelectorAll('.palette-content');
      allContents.forEach(content => content.classList.add('hidden'));
      
      const targetContent = document.getElementById(`${targetTab}-palettes`);
      if (targetContent) {
        targetContent.classList.remove('hidden');
      }
    });
  });
  
  // Apply palette functionality
  document.addEventListener('click', async function(e) {
    if (e.target.classList.contains('apply-palette-btn')) {
      const paletteName = e.target.getAttribute('data-palette');
      const palette = getPresetPalette(paletteName);
      
      if (!palette) {
        showToast('warning', 'Palette tidak ditemukan!');
        return;
      }
      
      
      
      // Create array of updates needed
      const updates = [];
      
      COLOR_VARIABLES.forEach(cv => {
        const presetValue = palette[cv.name];
        if (presetValue) {
          // Normalize values for comparison
          const currentNormalized = cv.value.trim().replace(/\s+/g, ' ').replace(/\s*\/\s*/, ' / ');
          const presetNormalized = presetValue.trim().replace(/\s+/g, ' ').replace(/\s*\/\s*/, ' / ');
          
          if (currentNormalized !== presetNormalized) {
            updates.push({
              variable: cv.name,
              value: presetValue
            });
          }
        }
      });
      
      if (updates.length === 0) {
        showToast('info', 'Tidak ada warna yang perlu diperbarui!');
        return;
      }
      
      
      
      try {
        // Apply all updates
        for (const update of updates) {
          const headers = {
            'Content-Type': 'application/json'
          };
          const csrfToken = getCSRFToken();
          if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
          }
          
          const response = await fetch('/api/brand-colors', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(update)
          });
          
          if (!response.ok) {
            throw new Error(`Failed to update ${update.variable}`);
          }
        }
        
        // Reload palette from backend
        const response = await fetch('/api/brand-colors');
        const data = await response.json();
        COLOR_VARIABLES = data;
        renderColorPaletteTable();
        
        // Reload CSS
        const link = document.querySelector('link[href*="base_css.css"]');
        if (link) {
          link.href = link.href.split('?')[0] + '?v=' + Date.now();
        }
        
        showToast('success', `Palette "${paletteName}" berhasil diterapkan!`);
      } catch (err) {
        console.error('Error applying palette:', err);
        showToast('error', 'Gagal menerapkan palette: ' + err.message);
      }
    }
  });
  

  
  // Add keyboard event listener for modal
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      const modal = document.getElementById('color-picker-modal');
      if (modal && !modal.classList.contains('hidden')) {
        closeColorPickerModal();
      }
    }
  });
}); 