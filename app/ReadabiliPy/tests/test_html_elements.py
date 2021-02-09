"""Tests for HTML elements."""
from pytest import mark
from .checks import (check_html_output_contains_text,
                     check_html_has_no_output,
                     check_html_output_does_not_contain_tag)


# Whitelisted HTML elements
def test_html_whitelist_article():
    """An article is a self-contained composition in a document."""
    check_html_output_contains_text("""
        <article>
        <header>
            <h2>Lorem ipsum dolor sit amet</h2>
            <p>Consectetur adipiscing elit</p>
        </header>
        <p>Vestibulum leo nulla, imperdiet a pellentesque ultrices aliquam.</p>
        </article>
    """)


def test_html_whitelist_aside():
    """An aside is a tangentially related section, used for pull-quotes."""
    check_html_output_contains_text("""
        <p>
           Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean
           libero neque, ullamcorper quis tristique.
        </p>
        <aside>
            <p>Aenean libero neque</p>
        </aside>
        <p>Pellentesque non sapien nec arcu facilisis gravida.</p>
    """)


def test_html_whitelist_blockquote():
    """The blockquote element contains quotes from another source."""
    check_html_output_contains_text("""
        <p>He began his list of "lessons" with the following:</p>
        <blockquote>
            One should never assume that his side of the issue will be
            recognized, let alone that it will be conceded to have merits.
        </blockquote>
        <p>He continued with a number of similar points, ending with:</p>
        <blockquote>
            Finally, one should be prepared for the threat of breakdown in
            negotiations at any given moment and not be cowed by the
            possibility.
        </blockquote>
        <p>We shall now discuss these points...</p>
    """)


def test_html_whitelist_caption():
    """The caption element represents the title of its parent table."""
    check_html_output_contains_text("""
        <p>The caption provides context to the table.</p>
        <table>
            <caption>
                Table 1. This shows the possible results of flipping two coins.
            </caption>
            <tbody>
                <tr>
                    <th></th>
                    <th>H</th>
                    <th>T</th>
                </tr>
            </tbody>
        </table>
    """, "<caption>Table 1. This shows the possible results of flipping two coins.</caption>")


def test_html_whitelist_colspan():
    """The colspan attribute allows cells to span multiple columns."""
    check_html_output_contains_text("""
        <table>
            <tr>
                <th>Month</th>
                <th>Savings</th>
            </tr>
            <tr>
                <td>January</td>
                <td>100</td>
            </tr>
            <tr>
                <td>February</td>
                <td>80</td>
            </tr>
            <tr>
                <td colspan="2">Sum: 180</td>
            </tr>
        </table>
    """, '<td colspan="2">Sum: 180</td>')


def test_html_whitelist_rowspan():
    """The rowspan attribute allows cells to span multiple rows."""
    check_html_output_contains_text("""
    <table>
        <tr>
            <th>Month</th>
            <th>Savings</th>
            <th>Savings for holiday!</th>
        </tr>
        <tr>
            <td>January</td>
            <td>100</td>
            <td rowspan="2">50</td>
        </tr>
        <tr>
            <td>February</td>
            <td>80</td>
        </tr>
    </table>
    """, '<td rowspan="2">50</td>')


def test_html_whitelist_div():
    """The div element has no special meaning."""
    check_html_output_contains_text("""
        <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean
            libero neque, ullamcorper quis tristique id pretium dapibus turpis.
        </p>
        <div>
            <p>Here is an example of using div for stylistic reasons.</p>
            <p>
                It marks several paragraphs which are in a different language
                from the rest of the text.
            </p>
        </div>
        <p>Pellentesque non sapien nec arcu facilisis gravida.</p>
    """)


def test_html_whitelist_dl():
    """The dl element is a description list."""
    check_html_output_contains_text("""
        <dl>
            <dt>Term 1</dt>
            <dd>Description 1</dd>
            <dt>Term 2</dt>
            <dd>Description 2</dd>
        </dl>
    """)


def test_html_whitelist_dd():
    """The dd element is a description in a description list."""
    check_html_output_contains_text("""
        <dl>
            <dt>Term 1</dt>
            <dd>Description 1</dd>
        </dl>
    """, "<dd>Description 1</dd>")


def test_html_whitelist_dt():
    """The dt element is a term in a description list."""
    check_html_output_contains_text("""
        <dl>
            <dt>Term 1</dt>
            <dd>Description 1</dd>
        </dl>
    """, "<dt>Term 1</dt>")


def test_html_whitelist_figure():
    """The figure element represents some self-contained flow content."""
    check_html_output_contains_text("""
        <p>In <a href="#figref">this figure</a> we see some code.</p>
        <figure id="figref">
            <figcaption>Listing 1. Code description.</figcaption>
            <pre>
                <code>Some formatted code lives here</code>
            </pre>
        </figure>
        <p>Further details are given in this paragraph.</p>
    """, """
        <figure id="figref">
            <figcaption>Listing 1. Code description.</figcaption>
            <pre>
                Some formatted code lives here
            </pre>
        </figure>
    """)


def test_html_whitelist_figcaption():
    """The figcaption element represents the caption of its parent figure."""
    check_html_output_contains_text("""
        <p>In <a href="#figref">this figure</a> we see some code.</p>
        <figure id="figref">
            <figcaption>Listing 1. Code description.</figcaption>
            <pre>
                <code>Some formatted code lives here</code>
            </pre>
        </figure>
        <p>Further details are given in this paragraph.</p>
    """, """
        <figcaption>Listing 1. Code description.</figcaption>
    """)


def test_html_whitelist_footer():
    """The footer element is the footer for its nearest ancestor section."""
    check_html_output_contains_text("""
        <p>
            A dolor sit amet, consectetur adipisicing elit, sed do eiusmod
            tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
            minim veniam, quis nostrud exercitation ullamco laboris nisi ut
            aliquip ex ea commodo consequat.
        </p>
        <footer>Text about author and date</footer>
    """)


def test_html_whitelist_h1():
    """The h1 element is often used for titles."""
    check_html_output_contains_text("""
        <h1>Title here</h1>
        <p>Some text following.</p>
    """)


def test_html_whitelist_h2_h3_h4_h5_h6():
    """hN elements represent headings for their sections in ranked order."""
    check_html_output_contains_text("""
        <h2>Second level</h2>
        <h3>Third level</h3>
        <h2>Also second-level</h2>
        <h3>Third level</h3>
        <h4>Fourth level</h4>
        <h5>Fifth level</h5>
        <h6>Bottom level</h6>
        <h4>Also fourth-level</h4>
        <h5>Also fifth level</h5>
    """)


def test_html_whitelist_header():
    """The header element contains introductory content for its ancestor."""
    check_html_output_contains_text("""
        <header>
            <p>Byline might live here for example.</p>
        </header>
        <p>
            A dolor sit amet, consectetur adipisicing elit, sed do eiusmod
            tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
            minim veniam, quis nostrud exercitation ullamco laboris nisi ut
            aliquip ex ea commodo consequat.
        </p>
    """)


def test_html_whitelist_li():
    """The li element defines an item in a list."""
    check_html_output_contains_text("""
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    """, """
        <li>Item 1</li>
        <li>Item 2</li>
    """)


def test_html_whitelist_main():
    """The main element contains content unique to its document."""
    check_html_output_contains_text("""
       <header>The header</header>
       <main>
            <p>A paragraph</p>
            <p>And another one</p>
        </main>
        <footer>The footer</footer>
    """, """
       <main>
            <p>A paragraph</p>
            <p>And another one</p>
        </main>
    """)


def test_html_whitelist_ol():
    """The ol element defines an unordered list."""
    check_html_output_contains_text("""
        <ol>
            <li>Item 1</li>
            <li>Item 2</li>
        </ol>
    """)


def test_html_whitelist_p():
    """The p element defines a paragraph."""
    check_html_output_contains_text("""
        <p>Nulla venenatis nulla porta, vestibulum felis ac, faucibus urna.</p>
        <p>
            Praesent imperdiet nec justo at blandit. Morbi ultrices urna in
            elementum viverra.
        </p>
    """)


def test_html_whitelist_pre():
    """The pre element represents a block of preformatted text."""
    check_html_output_contains_text("""
        <pre>
            Some preformatted   text lives  here
        </pre>
    """)


def test_html_whitelist_section():
    """The section element is a generic section of a document."""
    check_html_output_contains_text("""
        <section class="chapter">
            <h3 class="chaptertitle">My First Chapter</h3>
            <p>This is the first of my chapters. It doesn’t say much.</p>
            <p>But it has two paragraphs!</p>
        </section>
    """, """
        <section>
            <h3>My First Chapter</h3>
            <p>This is the first of my chapters. It doesn’t say much.</p>
            <p>But it has two paragraphs!</p>
        </section>
    """)


def test_html_whitelist_table():
    """The table element represents data with more than one dimension."""
    check_html_output_contains_text("""
        <table>
        <tbody>
            <tr>
                <td>Table contents</td>
            </tr>
        </tbody>
        </table>
    """, "<table><tbody><tr><td>Table contents</td></tr></tbody></table>")


def test_html_whitelist_tbody():
    """The tbody element represents a block of rows inside its parent table."""
    check_html_output_contains_text("""
        <table>
        <tbody>
            <tr>
                <td>Table body content</td>
            </tr>
        </tbody>
        </table>
    """, "<tbody><tr><td>Table body content</td></tr></tbody>")


def test_html_whitelist_thead():
    """The thead element contains rows forming the header of its table."""
    check_html_output_contains_text("""
        <table>
        <thead>
            <tr>
                <th>Header</th>
            </tr>
        </thead>
        </table>
    """, "<thead><tr><th>Header</th></tr></thead>")


def test_html_whitelist_tfoot():
    """The tfoot element contains the column summary rows of its table."""
    check_html_output_contains_text("""
        <table>
        <tfoot>
            <tr>
                <td>Sum of column</td>
            </tr>
        </tfoot>
        </table>
    """, "<tfoot><tr><td>Sum of column</td></tr></tfoot>")


def test_html_whitelist_tr():
    """The tr element represents a row in a table."""
    check_html_output_contains_text("""
        <table>
        <tr>
            <td>Table row content</td>
        </tr>
        </table>
    """, "<tr><td>Table row content</td></tr>")


def test_html_whitelist_td():
    """The td element represents a cell in a table."""
    check_html_output_contains_text("""
        <table>
        <tr>
            <td>Table cell content</td>
        </tr>
        </table>
    """, "<td>Table cell content</td>")


def test_html_whitelist_th():
    """The th element represents a header cell in a table."""
    check_html_output_contains_text("""
        <table>
        <tr>
            <th>Header text</th>
        </tr>
        </table>
    """, "<th>Header text</th>")


def test_html_whitelist_ul():
    """The ul element defines an unordered list."""
    check_html_output_contains_text("""
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    """)


# Blacklisted HTML elements
def test_html_blacklist_button():
    """The button element defines a clickable button."""
    check_html_has_no_output("""
        <button type="button">Click Me!</button>
    """)


def test_html_blacklist_datalist():
    """The datalist element represents a set of option elements."""
    check_html_has_no_output("""
        <datalist id=sexes>
            <option value="Female">
            <option value="Male">
        </datalist>
    """)


def test_html_blacklist_fieldset():
    """The fieldset element represents a set of form controls."""
    check_html_has_no_output("""
        <fieldset id=sexes>
            <option value="Female">
            <option value="Male">
        </fieldset>
    """)


def test_html_blacklist_form():
    """The form element is a user-interactive area of a document."""
    check_html_has_no_output("""
        <form>
            <div>
                <label>Customer name: <input></label>
            </div>
            <fieldset>
                <legend> Pizza Size </legend>
                <div><label><input type=radio name=size/>Small</label></div>
                <div><label><input type=radio name=size/>Medium</label></div>
                <div><label><input type=radio name=size/>Large</label></div>
            </fieldset>
        </form>
    """)


def test_html_blacklist_input():
    """The input element represents a typed data field."""
    check_html_has_no_output("""
        <input type=radio name=size/>
    """)


def test_html_blacklist_label():
    """The label element defines the label for another element."""
    check_html_has_no_output("""
        <label><input type=radio name=size/>Large</label>
    """)


def test_html_blacklist_legend():
    """The legend element has a caption for its parent fieldset."""
    check_html_output_does_not_contain_tag("""
        <fieldset>
            <legend>Pizza Size</legend>
            <label><input type=radio name=size/>Small</label>
        </fieldset>
    """, "legend")


def test_html_blacklist_meter():
    """The meter element represents a measurement within a known range."""
    check_html_has_no_output("""
        <meter value=6 max=8>6 blocks used (out of 8 total)</meter>
    """)


def test_html_blacklist_optgroup():
    """The optgroup element is a group of option elements."""
    check_html_output_does_not_contain_tag("""
        <select name="c">
            <optgroup label="8.01 Subject 1"/>
                <option value="8.01.1">Lecture 01: Topic 1</option>
                <option value="8.01.2">Lecture 02: Topic 2</option>
                <option value="8.01.3">Lecture 03: Topic 3</option>
            </optgroup>
            <optgroup label="8.02 Subject 2"/>
                <option value="8.02.1">Lecture 01: Topic 1</option>
                <option value="8.02.2">Lecture 02: Topic 2</option>
                <option value="8.02.3">Lecture 03: Topic 3</option>
            </optgroup>
        </select>
    """, "optgroup")


def test_html_blacklist_option():
    """The option element is an option in a select or datalist element."""
    check_html_output_does_not_contain_tag("""
        <datalist id=sexes>
            <option value="Female"/>
            <option value="Male"/>
        </datalist>
    """, "option")


def test_html_blacklist_output():
    """The output element is the result of a calculation or a user action."""
    check_html_output_does_not_contain_tag("""
        <form onsubmit="return false"
              oninput="o.value = a.valueAsNumber + b.valueAsNumber">
            <input name=a type=number step=any> +
            <input name=b type=number step=any> =
            <output name=o for="a b"></output>
        </form>
    """, "output")


def test_html_blacklist_progress():
    """The progress element represents the completion progress of a task."""
    check_html_output_does_not_contain_tag("""
        <section>
        <h2>Task Progress</h2>
        <p>
            Progress:
            <progress id="progbar" max=100><span>0</span>%</progress>
        </p>
        <script>
            var progressBar = document.getElementById('progbar');
            function updateProgress(amount) {
                progressBar.value += amount;
                progressBar.getElementsByTagName('span')[0]
                    .textContent = progressBar.value;
            }
        </script>
        <button type=button onclick="updateProgress(10)">Click here</button>
        </section>
    """, "progress")


def test_html_blacklist_select():
    """The select element is a control for selecting from a set of options."""
    check_html_output_does_not_contain_tag("""
        <select id="number" name="number">
            <option value="1"> One </option>
            <option value="2"> Two </option>
            <option value="3" selected> Three </option>
            <option value="4"> Four </option>
        </select>
    """, "select")


def test_html_blacklist_textarea():
    """The textarea element defines a multi-line text input control."""
    check_html_has_no_output("""
        <textarea>Some text here</textarea>
    """)


def test_html_blacklist_area():
    """The area element represents a corresponding area on an image map."""
    check_html_output_does_not_contain_tag("""
        <p>
            Please select a shape:
            <img src="shapes.png" usemap="#shapes" alt="Shapes."/>
            <map name="shapes">
                <area shape=rect coords="25,25,125,125" href="red.html"/>
                <area shape=circle coords="200,75,50" href="green.html"/>
            </map>
        </p>
    """, "area")


def test_html_blacklist_img():
    """The area element represents a corresponding area on an image map."""
    check_html_output_does_not_contain_tag("""
        <p>
            Please select a shape:
            <img src="shapes.png" usemap="#shapes" alt="Shapes."/>
            <map name="shapes">
                <area shape=rect coords="25,25,125,125" href="red.html"/>
                <area shape=circle coords="200,75,50" href="green.html"/>
            </map>
        </p>
    """, "area")


def test_html_blacklist_map():
    """The area element represents a corresponding area on an image map."""
    check_html_output_does_not_contain_tag("""
        <p>
            Please select a shape:
            <img src="shapes.png" usemap="#shapes" alt="Shapes."/>
            <map name="shapes">
                <area shape=rect coords="25,25,125,125" href="red.html"/>
                <area shape=circle coords="200,75,50" href="green.html"/>
            </map>
        </p>
    """, "area")


def test_html_blacklist_picture():
    """The picture element provides multiple sources for its img element."""
    check_html_output_does_not_contain_tag("""
        <picture>
            <source media="(min-width: 650px)" srcset="img_pink_flowers.jpg"/>
            <source media="(min-width: 465px)" srcset="img_white_flower.jpg"/>
            <img src="img_orange_flowers.jpg" style="width:auto;"/>
        </picture>
    """, "picture")


def test_html_blacklist_source():
    """The source element specifies an alternative source for a resource."""
    check_html_output_does_not_contain_tag("""
        <picture>
            <source media="(min-width: 650px)" srcset="img_pink_flowers.jpg"/>
            <source media="(min-width: 465px)" srcset="img_white_flower.jpg"/>
            <img src="img_orange_flowers.jpg" style="width:auto;"/>
        </picture>
    """, "source")


def test_html_blacklist_audio():
    """The audio element is a media element containing audio data."""
    check_html_output_does_not_contain_tag("""
        <audio controls>
            <source src="baa.ogg" type="audio/ogg">
            <source src="baa.mp3" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
    """, "audio")


def test_html_blacklist_track():
    """The track element specifies subtitles or other text for media."""
    check_html_output_does_not_contain_tag("""
        <video width="320" height="240" controls>
            <source src="film.mp4" type="video/mp4">
            <track src="subtitles_en.vtt" kind="subtitles"
                   srclang="en" label="English">
            <track src="subtitles_no.vtt" kind="subtitles"
                   srclang="no" label="Norwegian">
            Your browser does not support the video tag.
        </video>
    """, "track")


def test_html_blacklist_video():
    """The video element is a media element containing video data."""
    check_html_output_does_not_contain_tag("""
        <video width="320" height="240" controls>
            <source src="film.mp4" type="video/mp4">
            <source src="film.ogg" type="video/ogg">
            Your browser does not support the video tag.
        </video>
    """, "video")


def test_html_blacklist_embed():
    """The embed element provides an external (typically non-HTML) resource."""
    check_html_output_does_not_contain_tag("""
        <embed src="flashgame.swf" quality="high"/>
    """, "embed")


def test_html_blacklist_math():
    """The math element contains MathML elements."""
    check_html_output_does_not_contain_tag("""
        <p>
            <math>
                <mi>x</mi>
                <mo>=</mo>
                <mfrac>
                    <mrow>
                        <mo form="prefix">-</mo> <mi>b</mi>
                        <mo>±</mo>
                        <msqrt>
                            <msup> <mi>b</mi> <mn>2</mn> </msup>
                            <mo>-</mo>
                            <mn>4</mn> <mi>a</mi> <mi>c</mi>
                        </msqrt>
                    </mrow>
                    <mrow>
                        <mn>2</mn> <mi>a</mi>
                    </mrow>
                </mfrac>
            </math>
        </p>
    """, "math")


def test_html_blacklist_object():
    """The object element contains an external resource."""
    check_html_output_does_not_contain_tag("""
        <object data="flashgame.swf">
            <param name="quality" value="high">
        </object>
    """, "object")


def test_html_blacklist_param():
    """The param element defines plugin parameters for object elements."""
    check_html_output_does_not_contain_tag("""
        <object data="flashgame.swf">
            <param name="quality" value="high">
        </object>
    """, "param")


def test_html_blacklist_svg():
    """The svg element contains an embedded SVG graphic."""
    check_html_output_does_not_contain_tag("""
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1"
             width="5cm" height="5cm">
            <desc>A group of two rectangles</desc>
            <g id="group1" fill="red">
                <rect x="1cm" y="1cm" width="1cm" height="1cm"/>
                <rect x="3cm" y="1cm" width="1cm" height="1cm"/>
            </g>
        </svg>
    """, "svg")


def test_html_blacklist_details():
    """The details element is an expandable widget with additional context."""
    check_html_output_does_not_contain_tag("""
        <section class="progress window">
            <h1>Copying "Really Achieving Your Childhood Dreams"</h1>
            <details>
                <summary>Copying...
                    <progress max="100" value="25">25%</progress>
                </summary>
                <dl>
                    <dt>Transfer rate:</dt> <dd>452KB/s</dd>
                    <dt>Duration:</dt> <dd>01:16:27</dd>
                </dl>
            </details>
        </section>
    """, "details")


def test_html_blacklist_dialog():
    """The dialog element is a user-interactive area for performing."""
    check_html_output_does_not_contain_tag("""
        <p><b>Note:</b> The dialog tag is not supported in Edge.</p>
        <p>January <dialog open>This is an open dialog window</dialog></p>
        <p>February</p>
    """, "dialog")


def test_html_blacklist_summary():
    """The summary element provides a summary for its details element."""
    check_html_output_does_not_contain_tag("""
        <section class="progress window">
            <h1>Copying "Really Achieving Your Childhood Dreams"</h1>
            <details>
                <summary>Copying...
                    <progress max="100" value="25">25%</progress>
                </summary>
                <dl>
                    <dt>Transfer rate:</dt> <dd>452KB/s</dd>
                    <dt>Duration:</dt> <dd>01:16:27</dd>
                </dl>
            </details>
        </section>
    """, "summary")


def test_html_blacklist_canvas():
    """The canvas element provides a resolution-dependent bitmap canvas."""
    check_html_output_does_not_contain_tag("""
        <canvas id="myCanvas" width="200" height="100"></canvas>
    """, "canvas")


def test_html_blacklist_noscript():
    """The noscript element hides its children unless scripting is disabled."""
    check_html_output_does_not_contain_tag("""
        <p id="demo"></p>

        <script>
            document.getElementById("demo").innerHTML = "Hello JavaScript!";
        </script>

        <noscript>
            <p>Sorry, your browser does not support JavaScript!</p>
        </noscript>

        <p>Browsers without JavaScript support will show the noscript text.</p>
    """, "noscript")


def test_html_blacklist_script():
    """The script element contains dynamic scripts."""
    check_html_output_does_not_contain_tag("""
        <p id="demo"></p>

        <script>
            document.getElementById("demo").innerHTML = "Hello JavaScript!";
        </script>

        <noscript>
            <p>Sorry, your browser does not support JavaScript!</p>
        </noscript>

        <p>Browsers without JavaScript support will show the noscript text.</p>
    """, "script")


def test_html_blacklist_template():
    """The template element provides HTML fragments for use by scripts."""
    check_html_output_does_not_contain_tag("""
        <p>
            Click the button to fill the web page with one new DIV element for
            each item in an array.
        </p>

        <button onclick="showContent()">Show content</button>

        <template>
            <div>I like: </div>
        </template>

        <script>
            var myArr = ["preference 1", "preference 2"];
            function showContent() {
                var a, i;
                var temp = document.getElementsByTagName("template")[0];
                var item = temp.content.querySelector("div");
                for (i = 0; i < myArr.length; i++) {
                    a = document.importNode(item, true);
                    a.textContent += myArr[i];
                    document.body.appendChild(a);
                }
            }
        </script>
    """, "template")


def test_html_blacklist_data():
    """The data element has text and a machine-readable value attribute."""
    check_html_output_does_not_contain_tag("""
        <ul>
          <li><data value="21053">Cherry Tomato</data></li>
          <li><data value="21054">Beef Tomato</data></li>
          <li><data value="21055">Snack Tomato</data></li>
        </ul>
    """, "data")


def test_html_blacklist_link():
    """The link element provides access to other resources."""
    check_html_output_does_not_contain_tag("""
        <link rel="stylesheet" type="text/css" href="styles.css">
        <p>I am formatted with a linked style sheet</p>
    """, "link")


def test_html_blacklist_style():
    """The style element embeds style information in the document."""
    check_html_output_does_not_contain_tag("""
        <style>
            h1 {color:red;}
            p {color:blue;}
        </style>
        <p><strong>You add coins at your own risk.</strong></p>
    """, "style")


def test_html_blacklist_nav():
    """The nav element represents a section with navigation links."""
    check_html_output_does_not_contain_tag("""
        <nav>
            <a href="/html/">HTML</a> |
            <a href="/css/">CSS</a> |
            <a href="/js/">JavaScript</a> |
            <a href="/jquery/">jQuery</a>
        </nav>
    """, "nav")


def test_html_blacklist_br():
    """The br element represents a line break."""
    check_html_output_does_not_contain_tag("""
        <p>This text contains<br/>a line break.</p>
    """, "br")


def test_html_blacklist_hr():
    """The hr element represents a thematic break in text content."""
    check_html_output_does_not_contain_tag("""
        <h1>HTML</h1>
        <p>HTML is a language for describing web pages.....</p>

        <hr/>

        <h1>CSS</h1>
        <p>CSS defines how to display HTML elements.....</p>
    """, "hr")


# Special HTML elements
def test_html_special_q():
    """The q element contains quoted text."""
    check_html_output_contains_text(
        "<p>Some text <q>this bit is quoted</q> and now back to normal</p>",
        '<p>Some text "this bit is quoted" and now back to normal</p>'
    )


def test_html_special_sub():
    """The sub element contains subscript text."""
    check_html_output_contains_text(
        "<p>This text contains <sub>subscript</sub> text.</p>",
        "<p>This text contains _subscript text.</p>"
    )


def test_html_special_sup():
    """The sup element contains superscript text."""
    check_html_output_contains_text(
        "<p>This text contains <sup>superscript</sup> text.</p>",
        "<p>This text contains ^superscript text.</p>"
    )


# Remaining HTML elements - use a parametrized test here for simplicity
@mark.parametrize("element", ["a", "abbr", "address", "b", "bdi", "bdo",
                              "cite", "code", "del", "dfn", "em", "i", "ins",
                              "kbs", "mark", "marquee", "rb", "ruby", "rp",
                              "rt", "rtc", "s", "samp", "small", "span",
                              "strong", "time", "u", "var", "wbr"])
def test_html_remaining_element(element):
    """Simple standalone elements which can contain text.
       Check that the inner text is kept and the tag is discarded."""
    fragment = "<{0}>Lorem ipsum dolor sit amet</{0}>".format(element)
    check_html_output_contains_text(fragment, "Lorem ipsum dolor sit amet")
    check_html_output_does_not_contain_tag(fragment, element)
