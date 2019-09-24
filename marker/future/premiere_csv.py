from marker.marker import Scene


class PremiereCSV(Scene):
    def __init__(self):
        super().__init__()


    # @staticmethod
    # def markers_to_data(markers):
    #     if not markers: return None
    #
    #     # Premiere's format:
    #     # Marker Name	Description	In	Out	Duration	Marker Type
    #     # countdown		00;00;00;00	00;00;00;00	00;00;00;00	Comment
    #     # Note the two tabs after the name
    #
    #     data = OrderedDict()
    #     for line in markers.split("\n"):
    #         if not line or line.startswith('Marker Name'): continue
    #         (marker_name, control_data, in_point, out_point, _) = line.split("\t", 4)
    #         data[Filter.str_to_time(in_point.replace(';', ':'))] = {
    #             'in': Filter.str_to_time(in_point.replace(';', ':')),
    #             'out': Filter.str_to_time(out_point.replace(';', ':')),
    #             'name': marker_name,
    #             'control_data': control_data
    #         }
    #     Filter.set_out_points(data)
    #     return data
    #
    # @staticmethod
    # def set_out_points(data):
    #     # The out point of the current segment is the in point of the
    #     # _next_ segment.
    #     for idx, in_point in enumerate(data):
    #         marker = data[in_point]
    #         if marker['in'] == marker['out'] and idx < len(data):
    #             marker['out'] = list(data.values())[idx+1]['in']
