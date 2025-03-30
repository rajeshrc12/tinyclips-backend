def split_time_series(input_list, interval_length=2.0):
    """Process the input list and generate the desired output in one function."""
    output = []
    for interval in input_list:
        start = interval['start']
        end = interval['end']
        series = []
        current_start = start
        while current_start < end:
            current_end = min(current_start + interval_length, end)
            # If the remaining duration is less than the interval length, merge it with the previous interval
            if series and (current_end - current_start) < interval_length:
                # Merge with the previous interval
                series[-1]['end'] = current_end
            else:
                series.append({'start': current_start, 'end': current_end})
            current_start = current_end
        output.append({
            'start': start,
            'end': end,
            'series': series,
            'word': interval['word']
        })
    return output


def get_subtitle_with_image_index(data):
    count = 0
    subtitle_with_image_index = []
    for item in data:
        item["index"] = []
        for i, series in enumerate(item["series"]):
            series["index"] = count
            subtitle_with_image_index.append(series.copy())
            item["index"].append(count)
            count += 1
    return subtitle_with_image_index
