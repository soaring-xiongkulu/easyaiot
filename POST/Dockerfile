# syntax=docker/dockerfile:1
FROM golang:1.25-bookworm AS build
ARG TARGETARCH
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=${TARGETARCH} go build -o /out/post ./cmd/post \
 && CGO_ENABLED=0 GOOS=linux GOARCH=${TARGETARCH} go build -o /out/post-replay ./cmd/post-replay

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/post /usr/local/bin/post
COPY --from=build /out/post-replay /usr/local/bin/post-replay
COPY schemas /schemas
USER nonroot:nonroot
EXPOSE 8089
ENTRYPOINT ["/usr/local/bin/post"]
