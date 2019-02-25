$(function() {
  $.when(
    $.get("/srfi-map.json").fail(console.log),
    $.get("/srfi-to-symbol-map.json").fail(console.log)
  ).done(function(srfi_info_resp, srfi_to_symbol_resp) {
    var srfi_info_map = srfi_info_resp[0];
    var srfi_to_symbol_map = srfi_to_symbol_resp[0];
    $("#app").empty();
    var table = $("<table>").appendTo("#app");
    var srfi_numbers = Object.keys(srfi_info_map);
    for (var n = 0; n < srfi_numbers.length; n++) {
      var srfi_number = srfi_numbers[n];
      var info = srfi_info_map[srfi_number];
      var symbols = srfi_to_symbol_map[srfi_number];
      table.append(
        $("<tr>")
          .append($("<th>").append("SRFI " + srfi_number))
          .append(
            $("<th>").append(
              $("<a>")
                .attr("href", info.official_html_url)
                .text(info.title)
            )
          )
      );
      var ul = $("<ul>");
      if (symbols) {
        for (var i = 0; i < symbols.length; i++) {
          var symbol = symbols[i];
          ul.append($("<li>").append($("<code>").text(symbol)));
        }
      } else {
        ul.append(
          $("<li>")
            .addClass("error")
            .text("(No symbols found)")
        );
      }
      table.append(
        $("<tr>").append(
          $("<td>")
            .attr("colspan", 2)
            .append(ul)
        )
      );
    }
  });
});
