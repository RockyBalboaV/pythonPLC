station_name = self.args['station_name']

        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = YjStationInfo.query

        if station_id:
            query = query.filter_by(id=station_id)

        if station_name:
            query = query.filter_by(station_name=station_name)

        if page:
            query = query.paginate(page, per_page, False).items
        else:
            query = query.all()

        return query

    def information(self, models):
        if not models: