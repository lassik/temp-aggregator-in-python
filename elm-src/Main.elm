module Main exposing (Model(..), Msg(..), getSrfiList, init, main, srfiListDecoder, subscriptions, update, view, viewGif)

import Browser
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as JD exposing (Decoder, field, int, list, string)


main =
    Browser.element
        { init = init
        , update = update
        , subscriptions = subscriptions
        , view = view
        }


type alias Srfi =
    { number : Int
    , title : String
    , officialHtmlUrl : String
    , symbols : List String
    }


type Model
    = Failure
    | Loading
    | Success (List Srfi)


init : () -> ( Model, Cmd Msg )
init _ =
    ( Loading, getSrfiList )


type Msg
    = MorePlease
    | GotSrfiList (Result Http.Error (List Srfi))


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        MorePlease ->
            ( Loading, getSrfiList )

        GotSrfiList result ->
            case result of
                Ok url ->
                    ( Success url, Cmd.none )

                Err _ ->
                    ( Failure, Cmd.none )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none


view : Model -> Html Msg
view model =
    div [ style "font-family" "sans-serif" ]
        [ h2 [] [ text "Scheme documentation browser" ]
        , viewGif model
        ]


tdStyle =
    style "border" "1px solid black"


viewGif : Model -> Html Msg
viewGif model =
    case model of
        Failure ->
            div []
                [ text "Error loading documentation data from API"
                , button [ onClick MorePlease ] [ text "Try Again!" ]
                ]

        Loading ->
            text "Loading..."

        Success srfiList ->
            table [ tdStyle ]
                (List.concatMap
                    (\srfi ->
                        [ tr []
                            [ th [ tdStyle ] [ text ("SRFI " ++ String.fromInt srfi.number) ]
                            , th [ tdStyle ] [ a [ href srfi.officialHtmlUrl ] [ text srfi.title ] ]
                            ]
                        , tr []
                            [ td [ colspan 2, tdStyle ]
                                [ ul [] (List.map (\symbol -> li [] [ text symbol ]) srfi.symbols)
                                ]
                            ]
                        ]
                    )
                    srfiList
                )


getSrfiList : Cmd Msg
getSrfiList =
    Http.get
        { url = "/unstable/srfi"
        , expect = Http.expectJson GotSrfiList srfiListDecoder
        }


srfiListDecoder : Decoder (List Srfi)
srfiListDecoder =
    field "data" (list srfiDecoder)


srfiDecoder : Decoder Srfi
srfiDecoder =
    JD.map4 Srfi
        (field "number" int)
        (field "title" string)
        (field "official_html_url" string)
        (field "symbols" (list string))
