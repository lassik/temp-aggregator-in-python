module Main exposing (main)

import Browser
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as JD exposing (Decoder, field, int, list, string)
import String


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
    , implementations : List String
    }


type alias Implementation =
    { id : String
    , title : String
    , homepageUrl : String
    }


type Tab
    = Loading
    | Failure
    | SrfiTab
    | ImplTab


type alias Model =
    { tab : Tab, srfiList : List Srfi, implList : List Implementation }


init : () -> ( Model, Cmd Msg )
init _ =
    ( { tab = Loading, srfiList = [], implList = [] }
    , Cmd.batch [ getSrfiList, getImplList ]
    )


type Msg
    = SwitchToTab Tab
    | GotSrfiList (Result Http.Error (List Srfi))
    | GotImplList (Result Http.Error (List Implementation))


initialTab =
    SrfiTab


allLoaded model =
    if List.isEmpty model.srfiList || List.isEmpty model.implList then
        model

    else
        { model | tab = initialTab }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        SwitchToTab tab ->
            ( { model | tab = tab }, Cmd.none )

        GotSrfiList result ->
            case result of
                Ok srfiList ->
                    ( allLoaded { model | srfiList = srfiList }, Cmd.none )

                Err _ ->
                    ( { model | tab = Failure }, Cmd.none )

        GotImplList result ->
            case result of
                Ok implList ->
                    ( allLoaded { model | implList = implList }, Cmd.none )

                Err _ ->
                    ( { model | tab = Failure }, Cmd.none )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none


view : Model -> Html Msg
view model =
    div [ style "font-family" "sans-serif" ]
        [ h2 [] [ text "Scheme documentation browser" ]
        , case model.tab of
            Loading ->
                text "Loading..."

            Failure ->
                text "Error loading documentation data from API"

            SrfiTab ->
                viewTab (viewSrfiTab model.srfiList)

            ImplTab ->
                viewTab (viewImplTab model.implList)
        ]


viewTab contents =
    div []
        [ p []
            [ a
                [ href "https://github.com/lassik/schemedoc"
                , target "_blank"
                ]
                [ text "Source on GitHub" ]
            ]
        , hr [] []
        , p []
            [ button [ onClick (SwitchToTab SrfiTab) ]
                [ text "SRFIs" ]
            , button [ onClick (SwitchToTab ImplTab) ]
                [ text "Implementations" ]
            ]
        , contents
        ]


tdStyle =
    style "border" "1px solid black"


viewSrfiTab srfiList =
    table [ tdStyle ]
        (List.concatMap
            (\srfi ->
                [ tr []
                    [ th [ tdStyle ] [ text ("SRFI " ++ String.fromInt srfi.number) ]
                    , th [ tdStyle ]
                        [ a
                            [ href srfi.officialHtmlUrl
                            , target "_blank"
                            ]
                            [ text srfi.title ]
                        ]
                    ]
                , tr []
                    [ td [ colspan 2, tdStyle ]
                        [ text
                            ("Implementations: "
                                ++ (if List.isEmpty srfi.implementations then
                                        "(unknown)"

                                    else
                                        String.join ", " srfi.implementations
                                   )
                            )
                        ]
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


viewImplTab implList =
    ul []
        (List.map
            (\impl ->
                li []
                    [ a [ href impl.homepageUrl, target "_blank" ]
                        [ text impl.title ]
                    ]
            )
            implList
        )


getSrfiList : Cmd Msg
getSrfiList =
    Http.get
        { url = "/unstable/srfi"
        , expect = Http.expectJson GotSrfiList srfiListDecoder
        }


srfiListDecoder : Decoder (List Srfi)
srfiListDecoder =
    field "data" (JD.list srfiDecoder)


srfiDecoder : Decoder Srfi
srfiDecoder =
    JD.map5 Srfi
        (field "number" int)
        (field "title" string)
        (field "official_html_url" string)
        (field "symbols" (JD.list string))
        (field "implementations" (JD.list string))


getImplList : Cmd Msg
getImplList =
    Http.get
        { url = "/unstable/implementation"
        , expect = Http.expectJson GotImplList implListDecoder
        }


implListDecoder : Decoder (List Implementation)
implListDecoder =
    field "data" (JD.list implDecoder)


implDecoder : Decoder Implementation
implDecoder =
    JD.map3 Implementation
        (field "id" string)
        (field "title" string)
        (field "homepage_url" string)
