from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from train.models import TrainType, Train, Station, Route, Journey, Order, Crew
from train.serializers import (
    TrainTypeSerializer,
    TrainSerializer,
    StationSerializer,
    RouteSerializer,
    RouteDetailSerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    OrderSerializer,
    CrewDetailSerializer,
    CrewListSerializer,

)


class TrainTypeViewSet(viewsets.ModelViewSet):
    serializer_class = TrainTypeSerializer
    queryset = TrainType.objects.all()


class TrainViewSet(viewsets.ModelViewSet):
    serializer_class = TrainSerializer
    queryset = Train.objects.select_related("train_type")


class StationViewSet(viewsets.ModelViewSet):
    serializer_class = StationSerializer
    queryset = Station.objects.all()


class RouteViewSet(viewsets.ModelViewSet):
    serializer_class = RouteSerializer
    queryset = Route.objects.select_related("source", "destination")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RouteDetailSerializer
        return self.serializer_class


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class JourneyViewSet(viewsets.ModelViewSet):
    serializer_class = JourneyListSerializer
    queryset = Journey.objects.select_related(
        "train__train_type",
        "route__source",
        "route__destination",
    ).prefetch_related("tickets").annotate(
        tickets_available=(
                F("train__cargo_num") * F("train__places_in_cargo")
                - Count("tickets")
        )
    )
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return JourneyDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")

        queryset = self.queryset

        if start_date and not end_date:
            queryset = queryset.filter(departure_time__date=start_date)

        if start_date and end_date:
            queryset = queryset.filter(
                departure_time__range=(start_date, end_date)
            )
        if source:
            queryset = queryset.filter(route__source__name__icontains=source)

        if destination:
            queryset = queryset.filter(
                route__destination__name__icontains=destination
            )

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("tickets__journey__train")
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CrewViewSet(viewsets.ModelViewSet):
    serializer_class = CrewListSerializer
    queryset = Crew.objects.prefetch_related("journeys__route")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CrewDetailSerializer
        return self.serializer_class
