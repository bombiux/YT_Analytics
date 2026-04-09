import pandas as pd

def get_top_5_videos_per_channel(csv_file_path, output_file='top_videos_report.csv'):
    """
    Reads a CSV file and returns the 5 videos with the highest view counts for each channel.
    Also saves the result to a CSV file.

    Args:
        csv_file_path (str): Path to the CSV file
        output_file (str): Path to save the output CSV

    Returns:
        dict: Dictionary with channel names as keys and top 5 videos as values
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Group by ChannelName and get top 5 videos for each channel
    top_videos_by_channel = {}
    all_top_videos = []

    for channel in df['ChannelName'].unique():
        channel_data = df[df['ChannelName'] == channel]
        top_5_for_channel = channel_data.nlargest(5, 'ViewCount')
        top_videos_by_channel[channel] = top_5_for_channel[['ChannelName', 'VideoType', 'Title', 'ViewCount', 'VideoID']]
        all_top_videos.append(top_5_for_channel)

    # Save to CSV
    if all_top_videos:
        pd.concat(all_top_videos).to_csv(output_file, index=False)
        print(f"\n[OK] Reporte CSV generado: {output_file}")

    return top_videos_by_channel

# File path
csv_file = 'all_videos_report.csv'

# Get top 5 videos per channel
top_videos_by_channel = get_top_5_videos_per_channel(csv_file)

# Display the results
for channel, videos in top_videos_by_channel.items():
    print(f"\nTop 5 Most Viewed Videos for Channel: {channel}")
    print("="*60)
    for index, row in videos.iterrows():
        print(f"Video Type: {row['VideoType']}")
        print(f"Title: {row['Title']}")
        print(f"Views: {row['ViewCount']:,}")
        print("-"*40)

# Al final, enviamos el reporte por Telegram
import telegram_sender
telegram_sender.format_and_send_reports(top_videos_by_channel)