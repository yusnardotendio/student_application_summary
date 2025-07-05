import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Define the project phases and their durations based on the timeline
tasks = [
    {"Task": "Phase 1: Team Formation & Planning", "Start": "2025-05-05", "Duration": 7, "Phase": 1},
    {"Task": "Phase 2: Core Backend Development", "Start": "2025-05-12", "Duration": 20, "Phase": 2},
    {"Task": "Phase 3: Frontend & UI (Gradio)", "Start": "2025-05-24", "Duration": 15, "Phase": 2},
    {"Task": "Phase 4: Integration & Refinement", "Start": "2025-06-09", "Duration": 20, "Phase": 3},
    {"Task": "Phase 5: Testing & Finalization", "Start": "2025-06-30", "Duration": 10, "Phase": 4},
    {"Task": "Phase 6: Documentation", "Start": "2025-07-10", "Duration": 14, "Phase": 5}
   
]

# Convert string dates to datetime objects and calculate end dates
for task in tasks:
    task["Start"] = datetime.strptime(task["Start"], "%Y-%m-%d")
    task["End"] = task["Start"] + timedelta(days=task["Duration"])

# Define TUM-inspired colors for different phases
phase_colors = {
    1: '#005293',  # Darkest TUM Blue for Planning
    2: '#0065BD',  # Primary TUM Blue for Core Development
    3: '#64A0C8',  # Lighter Blue for Integration
    4: '#98C6EA',  # Very Light Blue for Testing
    5: '#A1B7C4'   # Muted Grey-Blue for Finalization
}

# Create the plot
fig, ax = plt.subplots(figsize=(14, 7))

# Plot the tasks as horizontal bars
for task in tasks:
    color = phase_colors.get(task["Phase"], 'grey') # Get color from dict
    ax.barh(task["Task"], task["Duration"], left=task["Start"], color=color, edgecolor='black', linewidth=0.5, zorder=3)

# Invert y-axis to have the first task on top
ax.invert_yaxis()

# Format the date axis
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
plt.xticks(rotation=45, ha="right")

# Set the date range for the x-axis
start_date = datetime.strptime("2025-05-01", "%Y-%m-%d")
end_date = datetime.strptime("2025-07-25", "%Y-%m-%d")
ax.set_xlim(start_date, end_date)

# Set title and axis labels with bold font
ax.set_title("Project Timeline: Intelligent Evaluation Assistant for TUM", fontsize=16, fontweight='bold')
ax.set_xlabel("Date", fontsize=12, fontweight='bold')
ax.set_ylabel("Project Phase", fontsize=12, fontweight='bold')

# # Add a vertical line for a key milestone, e.g., "Mid-Project Review"
# milestone_date = datetime.strptime("2025-06-16", "%Y-%m-%d")
# ax.axvline(milestone_date, color="#d95319", linestyle='--', linewidth=2, zorder=4)
# ax.text(milestone_date + timedelta(days=1), 4.5, 'Mid-Project Review', rotation=90, va='bottom', color="#d95319", fontsize=10)

# Add a grid for better readability
ax.grid(axis='x', linestyle=':', color='gray', alpha=0.7)

# Adjust layout to prevent labels from being cut off
plt.tight_layout()

# Show the plot
plt.show()