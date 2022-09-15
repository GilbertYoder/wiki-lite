
class LayoutPage {

    constructor() {

    }

    init_data() {
        async function fetch_data() {
            let markdown = "";
            if (pagename) {
                markdown = await (await fetch('/wiki_page/markdown/' + relativepath + window.location.search)).text();
            }
            return markdown;
        }
        fetch_data().then((markdown) => {
            this.load_page(markdown)
        })
    }

    load_page(markdown) {
        console.log("Loading Page");
        let layout_page = this;

        let search_term = (new URLSearchParams(window.location.search)).get('text');

        const app = {
            data() {
                return {

                    commit_message: "misc changes",

                    page_sha: "",

                    search_term: search_term,
                    show_palette: false,
                    command: "",
                    user_input: "",
                    user_input_title: "",

                    markdown_template: markdown,
                    layout_page: layout_page,

                    edit_mode: false,
                    backup_markdown: "",
                }
            },
            methods: {
                enter_edit_mode() {
                    this.backup_markdown = this.markdown_template;
                    this.edit_mode = true;

                    this.$nextTick(() => {
                        let text_area = document.getElementById('wiki_text_area');
                        text_area.style.visibility = "visible";

                        text_area.addEventListener('keydown', function (e) {
                            if (e.key == 'Tab') {
                                e.preventDefault();
                                var start = this.selectionStart;
                                var end = this.selectionEnd;
                                this.value = this.value.substring(0, start) +
                                    "\t" + this.value.substring(end);
                                this.selectionStart =
                                    this.selectionEnd = start + 1;
                            }
                        });

                        text_area.style.height = "";
                        text_area.style.height = text_area.scrollHeight + "px";
                    })
                },
                save_edit_mode() {
                    async function save(data) {
                        return await (await fetch('/save_page/' + relativepath + window.location.search, { method: 'POST', body: data })).text();
                    }

                    let post_data = {
                        "data": this.markdown_template,
                        "commit_message": this.commit_message
                    }

                    save(JSON.stringify(post_data)).then((res) => {
                        // this.html_template = res;
                        // this.edit_mode = false;
                        window.location.reload();
                    })
                },
                view_html() {
                    this.edit_mode = false;
                },
                cancel_edit_mode() {
                    this.markdown_template = this.backup_markdown;
                    this.edit_mode = false;
                },
                new_file() {
                    this.command = "new_page";
                    this.user_input = "";
                    this.user_input_title = "New page name:";
                    this.get_user_input();
                },
                new_folder() {
                    this.command = "new_folder";
                    this.user_input = "";
                    this.user_input_title = "New folder name";
                    this.get_user_input();
                },
                create_page() {
                    this.command = "new_page"
                    this.user_input = pagename;
                    this.execute_cmd();
                },
                delete_page() {
                    this.command = "delete_page";
                    this.execute_cmd();
                },
                get_user_input() {
                    let pr = prompt(this.user_input_title);
                    if (pr) {
                        this.user_input = pr; 
                        this.execute_cmd()
                    }
                },
                view_version(sha) {
                    

                    async function fetch_data(sha) {
                        let params = sha != '' ? "?commit_sha=" + sha : ""
                        let html = await (await fetch('/wiki_page/html/' + relativepath + params)).text();
                        let markdown = await (await fetch('/wiki_page/markdown/' + relativepath + params)).text();
                        return { html: html, markdown: markdown };
                    }
                    fetch_data(sha).then((res) => {
                        this.page_sha = sha;
                        document.getElementById("wiki_rendered").innerHTML = res.html;
                        this.markdown_template = res.markdown;
                    })

                    console.log(sha);
                },
                execute_cmd() {
                    console.log(this.command);
                    let cmd_split = this.command.split(":", 2);
                    let cmd = this.command;
                    let arg = this.user_input;

                    async function ajx(url) {
                        return await (await fetch(url)).text();
                    }

                    if (cmd == "new_page") {
                        arg = arg.split(".")[0];
                        let path = relativepath.split("/").slice(0, -1).join("/") + "/" + arg + ".md"
                        ajx("/wiki_page/create_page/" + path).then((res) => {
                            console.log(res);
                            window.location.href = "/wiki/" + path;
                        });
                    }

                    if (cmd == "new_folder") {
                        let path = relativepath.split("/").slice(0, -1).join("/") + "/" + arg
                        ajx("/wiki_page/create_folder/" + path).then((res) => {
                            console.log(res);
                            location.reload();
                        });
                    }

                    if (cmd == "delete_page") {
                        let should_delete = confirm("Are you sure you wish to delete this page? This action cannot be undone.")
                        if (!should_delete) return;
                        ajx("/wiki_page/delete_page/" + relativepath).then((res) => {
                            window.location.href = "home.md";
                        });
                    }
                },
                toggle_palette() {
                    if (this.show_palette) {
                        this.show_palette = false;
                        return;
                    }
                    this.show_palette = true;
                    this.$nextTick(() => {
                        document.getElementById("action_popup").style.visibility = "visible";
                        document.getElementById('command_input').focus();
                    })
                }
            },
            mounted() {
                document.onkeydown = (e) => {
                    if (!pagename) return;
                    if (e.ctrlKey && e.key === 's') {
                        e.preventDefault();
                        if (this.edit_mode) {
                            this.save_edit_mode();
                        }
                    }
                    if (e.ctrlKey && e.key === 'e') {
                        e.preventDefault();
                        this.enter_edit_mode();
                    }
                }
            },
            delimiters: ['[[', ']]'],
        }

        this.VueApp = Vue.createApp(app);
        this.VueApp.mount("body");
    }
}

page = new LayoutPage()
page.init_data()

function resize_textarea() {
    scroll = document.documentElement.scrollTop || document.body.scrollTop;
    let text_area = document.getElementById('wiki_text_area');
    text_area.style.height = "";text_area.style.height = text_area.scrollHeight + "px"
    document.documentElement.scrollTop = document.body.scrollTop = scroll;
}