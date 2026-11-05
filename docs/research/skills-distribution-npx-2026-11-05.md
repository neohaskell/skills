# Distribución de las skills NeoHaskell mediante `npx skills`

Investigación del 5 de noviembre de 2026. Ticket: [Verificar instalación, versiones y actualizaciones con npx skills](https://plane.p.egregore.io/egregore/projects/5535680e-e3f6-4023-b400-2b27544130e2/issues/4232476b-2646-4fc6-8111-e745ebeb57fd/).

## Resolución propuesta

Es viable distribuir directamente este repositorio mediante **`npx skills`**, conservar las skills instaladas y su lock en el Git de cada aplicación, y actualizar mediante un cambio explícito revisable. No hace falta publicar un paquete npm propio para ese recorrido.

Recomiendo instalar una **release de la colección fijada a un SHA completo**, publicar tags legibles que señalen esos commits y fijar también la versión probada del instalador. Cambiar de release se haría ejecutando `add` otra vez con el nuevo ref y los destinos explícitos `codex claude-code`, dentro de una rama de actualización. Es una propuesta para la decisión posterior; este estudio no adopta ni implementa esa política.

`check` y `update` conservan el ref registrado. Seguir una rama permite recibir sus cambios mediante `update`; fijar un tag o SHA conserva esa revisión y **no busca el siguiente tag semántico**. Las personalizaciones dentro de una skill gestionada pueden perderse cuando se reinstala. La instalación selectiva tampoco resuelve dependencias entre skills. Estos contratos condicionan el diseño del catálogo y del procedimiento de actualización. [Código de actualización](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/update.ts#L948-L1060), [instalador](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/installer.ts#L198-L206), [selección](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/add.ts#L2190-L2250).

## Alcance y evidencia

Se consultaron documentación oficial, registro npm y código fuente primario. La versión publicada observada es **`skills@1.7.6`**, cuyo `gitHead` es `7a5e920bead4b1039a6d6df5d7e1163b7b09423a`; requiere **Node >=22.20.0**. Las pruebas usaron su paquete npm con Node 24.21.0. Se fijó el checkout de investigación a ese commit: `main` del instalador ya estaba por delante y no se utilizó para adjudicar comportamiento a 1.7.6. [Metadatos npm de la versión](https://registry.npmjs.org/skills/1.7.6), [package.json fijado](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/package.json).

Se probaron consumidores temporales, un repositorio sintético de dos skills y la descarga real de las 27 skills de `neohaskell/skills` en `89cca8fdbb5ad73252ff107779ade7ee30f25f4f`. Se aisló el estado del CLI con `XDG_STATE_HOME`, se desactivó telemetría y no se ejecutó ninguna instalación global. No se modificó el checkout del usuario, ni se inició Codex o Claude Code, ni se accedió a ningún archivo de CIOS.

Por tanto, **instalación y conservación de archivos están comprobadas; comportamiento del agente al ejecutar las skills queda para las pruebas de aceptación**. La elección de agentes soportados en esta primera versión ya está fijada por el usuario: Codex y Claude Code.

## Formatos de origen y versiones

| Entrada | Interpretación comprobada en código |
| --- | --- |
| `neohaskell/skills` | Repositorio GitHub; al omitir ref se clona su revisión por defecto. |
| `neohaskell/skills#v1.0.0` | Tag o rama `v1.0.0`. Usar comillas en los ejemplos de shell. |
| `neohaskell/skills#<SHA completo de 40 caracteres>` | Commit concreto. Instalación real desde GitHub probada. |
| `https://github.com/neohaskell/skills/tree/v1.0.0` | Ref dentro de una URL GitHub. |
| `neohaskell/skills@event-modeling` | Filtro por **nombre de skill**, no versión de la colección. |
| `neohaskell/skills#v1.0.0@event-modeling` | Ref y filtro de skill; para documentación prefiero `#ref --skill nombre`. |
| `./checkout-local` | Directorio local; útil en CI de publicación, pero sus entradas no entran en la actualización remota normal. |

Los fragmentos `#ref` admiten ramas con `/` sin la ambigüedad de una URL `/tree/<rama>/<ruta>`. El clone intenta primero rama/tag y permite recuperar un SHA completo si no encuentra ese nombre. No debe prometerse que cualquier SHA abreviado funciona. [Parser de fragmentos](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/source-parser.ts#L281-L319), [parser `@skill`](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/source-parser.ts#L532-L553), [clonado y fallback SHA](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/git.ts).

Existen dos versiones distintas: `npx skills@1.7.6` fija el **instalador**; `neohaskell/skills#<ref>` fija el **contenido**. Un tag Git puede moverse si el mantenedor lo permite; el SHA completo ofrece una identidad inequívoca. La consulta de tags de `neohaskell/skills` no devolvió ninguno durante este estudio, por lo que `v1.0.0` es un ejemplo futuro y no una release existente.

Ejemplo ejecutado con la revisión real disponible:

```sh
npx --yes skills@1.7.6 add   'neohaskell/skills#89cca8fdbb5ad73252ff107779ade7ee30f25f4f'   --skill '*' --agent codex claude-code --yes
```

`--yes` de npm evita su confirmación de descarga; el último `--yes` corresponde al instalador. Ejecutarlo desde la raíz Git de la aplicación selecciona el alcance de proyecto: no se añade `--global`. No usar `--all` como sustituto, porque también selecciona todos los agentes. [Referencia oficial de comandos](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/docs/commands.md).

## Archivos instalados, recursos y dependencias

Con ambos agentes explícitos, el modo normal produjo:

```text
aplicacion/
├── .agents/skills/event-modeling/
│   ├── SKILL.md
│   └── references/event-model.schema.json
├── .claude/skills/event-modeling -> ../../.agents/skills/event-modeling
└── skills-lock.json
```

Codex usa `.agents/skills`. Claude Code recibe un enlace relativo desde `.claude/skills`; `--copy` produjo copias independientes en ambos destinos. Para este conjunto de agentes recomiendo validar el modo normal, que mantiene una única copia canónica en el proyecto. Es una recomendación de distribución, no una afirmación de que todos los sistemas operativos acepten enlaces del mismo modo. [Destinos de agentes](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/agents.ts#L160-L169), [Codex](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/agents.ts#L229-L235), [instalación de carpetas](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/installer.ts#L324-L455).

Se conservaron `references/`, `scripts/` y `agents/openai.yaml` en la fixture. El instalador copia recursivamente los recursos de la carpeta de la skill. Un enlace interno se convirtió en un archivo con su contenido; un enlace que salía hacia una skill hermana se omitió. Por tanto, enlazar mediante symlinks a documentación compartida fuera de la carpeta **no empaqueta esa documentación**. Los enlaces Markdown entre skills siguen dependiendo de que ambas estén instaladas. [Copia y límites de symlinks](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/installer.ts#L527-L599).

La instalación de `alpha` no instaló `beta`, aunque alpha incluyera un enlace a beta y `metadata.dependencies: [beta]`. Ese campo no constituye un contrato de resolución del CLI. Debemos decidir entre un conjunto completo cerrado a dependencias, unidades selectivas realmente autónomas o una capa propia que materialice el cierre. Para una primera versión sencilla recomiendo **instalar el catálogo de aplicaciones completo y validar todos sus enlaces después de instalar**, dejando la instalación selectiva como capacidad avanzada solo donde esté comprobada. [Selección exacta de skills](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/add.ts#L2190-L2250), [tipo de skill](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/types.ts#L80-L94).

El catálogo instalable debe contener solo la colección soportada. Un snapshot de upstream, ejemplos con `SKILL.md` o herramientas internas situados en rutas que el descubrimiento recorre pueden acabar expuestos al usuario. El CLI conoce varios directorios de skills y tiene búsqueda más profunda; no debemos confiar en que una carpeta adicional quede invisible. Registrar procedencia, commits upstream y licencias es una responsabilidad de este repositorio, separada del lock generado en cada consumidor. [Descubrimiento](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/skills.ts#L245-L345).

## Locks, alcance de actualización y restauración

| Contrato | Resultado |
| --- | --- |
| Proyecto | `skills-lock.json`, esquema v1, preparado para Git; registra origen, `ref` cuando existe, ruta de skill y SHA-256 del contenido. |
| Global | `~/.agents/.skill-lock.json`, esquema v3; con `XDG_STATE_HOME`, usa `$XDG_STATE_HOME/skills/.skill-lock.json`. Es estado del usuario, no el lock del proyecto. |
| `check -p` | Comprueba las skills del lock del directorio actual sin reinstalarlas. Devolvió 1 cuando la rama tenía cambios y 0 con el tag fijo. |
| `update -p` | Actualiza las entradas de proyecto comprobables contra sus refs registrados. No cambia automáticamente de tag ni enumera una nueva release semántica. |
| `update nombre` sin alcance | Puede resolver ambos ámbitos, proyecto y global. Usar siempre el alcance explícito en documentación. |
| Nuevas/borradas skills | Actualizar las instaladas no equivale a reconciliar todo el catálogo: no promete instalar nuevas skills; las eliminaciones upstream se omiten en modo no interactivo. |

Fuentes: [lock local](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/local-lock.ts#L1-L71), [lock global](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/skill-lock.ts#L6-L74), [selección de alcance](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/update.ts#L216-L235), [eliminaciones](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/update.ts#L355-L387), [exit codes de check](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/update.ts#L1103-L1169).

La entrada real de `event-modeling` quedó así:

```json
{
  "source": "neohaskell/skills",
  "ref": "89cca8fdbb5ad73252ff107779ade7ee30f25f4f",
  "sourceType": "github",
  "skillPath": "skills/event-modeling/SKILL.md",
  "computedHash": "3824ab110a85f2aa1cc7450bd0a4957b7f898b8301b0be108e3898e37394c565"
}
```

El hash detecta un cambio de contenido, pero por sí solo no proporciona el commit desde el que recuperarlo. Al seguir una rama mutable el lock no convierte esa rama en un SHA inmutable; para reproducibilidad debe guardarse un ref fijo o el contenido instalado en Git. [Modelo del lock](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/local-lock.ts#L12-L55).

Además, `update` vuelve a detectar agentes; el lock no conserva una lista general de destinos por skill. El modo de copia sí puede registrarse, pero eso no garantiza reinstalar exactamente para los dos agentes elegidos inicialmente. **Reejecutar `add` con agentes explícitos evita depender de esta detección** durante una actualización de release. [Resolución de destinos](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/update.ts#L77-L102), [campos locales](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/local-lock.ts#L12-L55).

`skills install`/`experimental_install` puede restaurar a partir del lock, pero su implementación instala en la ubicación universal `.agents/skills`; **no reconstruye por sí sola los destinos específicos de Claude Code**. Su modo congelado compara contenido y puede impedir aceptar cambios del origen, pero tampoco inventa un commit inexistente en el lock. En esta versión no documentaría “basta el lock y `install`” como recuperación completa de ambos agentes. Versionar la copia canónica y los enlaces, o repetir el `add` fijado con los agentes elegidos, ofrece un contrato comprobable. [Restauración desde lock](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/install.ts#L14-L110).

## Ediciones locales, revisión y rollback

En la prueba de actualización de rama se añadió una personalización a `SKILL.md` en el consumidor y se cambió solo una referencia upstream. `update -p --yes` reinstaló la skill entera: incorporó la referencia nueva y eliminó la personalización. El tag fijado permaneció en v1. La implementación limpia la carpeta antes de copiar y no ofrece fusión de tres vías. También puede informar de que está al día cuando el origen coincide con el lock, aunque el consumidor haya editado sus archivos: compara el origen con el hash registrado, no garantiza auditoría de modificaciones locales. [Comparación](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/update.ts#L1033-L1057), [limpieza del destino](https://github.com/vercel-labs/skills/blob/7a5e920bead4b1039a6d6df5d7e1163b7b09423a/src/installer.ts#L198-L206).

Procedimiento propuesto para la implementación:

1. Comprobar que las rutas gestionadas están limpias y crear una rama de actualización. Conservar las extensiones propias con nombres/rutas distintos; si existen cambios locales dentro de las skills gestionadas, resolverlos explícitamente antes de reinstalar.
2. Elegir una release, resolver su SHA y ejecutar `add` con ese ref, el catálogo completo y `--agent codex claude-code`. El mismo comando sirve para instalación inicial y cambio explícito de versión.
3. Revisar `git diff` sobre contenido, enlaces y `skills-lock.json`; ejecutar validación de enlaces y aceptación de ambos agentes. Tratar eliminaciones/renombres como una migración explícita de las rutas que posee el paquete, sin borrar skills ajenas.
4. Confirmar el cambio en un commit. El rollback consiste en revertir ese commit junto con su lock y enlaces. Se probó ese recorrido: recuperó el recurso v1 y dejó el consumidor limpio.
5. Registrar procedencia de las copias adaptadas en este repositorio; una sincronización con NeoHaskell debe producir su propio cambio revisado. Actualizar consumidores y sincronizar upstream son operaciones diferentes.

No existe aquí un requerimiento de servicio de actualización automática. Se necesita documentación de releases y un procedimiento explícito; un pequeño wrapper solo estaría justificado para controlar propiedad de archivos, comprobar cambios locales y reconciliar nuevas/eliminadas skills. No es necesario sustituir el instalador para empezar.

## Pruebas ejecutadas y límites

| Prueba aislada con 1.7.6 | Resultado observado |
| --- | --- |
| Instalar `alpha` desde directorio local para ambos agentes | Una copia canónica y enlace relativo de Claude; `beta` ausente. |
| Instalar recursos propios | `references/`, `scripts/` y `agents/openai.yaml` presentes. |
| Enlaces de recursos | Enlace interno convertido a contenido; enlace hacia fuera omitido. |
| `--copy` | Carpetas independientes de Codex y Claude, sin enlace Claude. |
| Tag, rama y SHA completo en repositorio Git sintético | Tres instalaciones correctas. |
| `check -p` tras cambiar la rama upstream | Exit 1 con rama; exit 0 con tag fijo. |
| `update -p --yes` tras cambiar la rama | Contenido nuevo instalado; personalización local perdida. |
| Git revert del commit de actualización | Contenido v1 restaurado; estado Git limpio. |
| GitHub real, revisión `89cca8f…`, catálogo completo | 27 skills instaladas, 27 refs SHA registrados, referencias conservadas. |
| `check -p` del consumidor GitHub fijado | Exit 0. |

Para reproducir el ensayo de actualizaciones sin publicar fixtures: crear un repositorio temporal con dos commits y tags, dos skills y un recurso; proporcionar al CLI una URL HTTPS `.git` sintética y configurar `git -c url.<file-url>.insteadOf=<synthetic-url>` mediante `GIT_CONFIG_COUNT/KEY/VALUE` solo en los procesos de prueba. Se usó `protocol.file.allow=always` únicamente en esos procesos. Así se ejercita el parser de refs y la ruta Git real, sin escribir configuración Git global ni usar perfiles reales. Los primeros intentos con `file://...#ref` no funcionaron porque el parser no separa el fragmento para ese formato; se corrigió la fixture para usar un formato Git soportado. No se presenta `file://...#ref` como sintaxis admitida.

Reproducción mínima del contrato público: ejecutar el ejemplo SHA anterior en un directorio temporal, inspeccionar `skills-lock.json` y `.claude/skills/event-modeling`, y ejecutar `npx --yes skills@1.7.6 check -p`. Para la política de tags, sustituir el SHA por un tag real cuando exista y repetir `add` para el nuevo tag elegido.

No se probó la instalación global, Windows, ejecución real de agentes, compatibilidad semántica de las skills ni migración de toda la colección importada. Esas validaciones quedan fuera de esta investigación. Los hechos de alcance global, restauración y detección de agentes se sustentan en el código fijado; las tablas de pruebas distinguen las observaciones ejecutadas.

## Consecuencias para el plan de implementación

La tarea de distribución debe producir un catálogo de aplicaciones instalable y cerrado a sus dependencias, tags/releases con procedencia verificable, instrucciones de instalación y actualización explícitas y pruebas con un consumidor vacío. La tarea de organización debe conservar todos los recursos bajo sus dueños y validar enlaces en el resultado instalado. La tarea de aceptación debe comprobar Codex y Claude Code con la versión concreta del CLI, incluido que no se pierdan recursos ni personalizaciones ajenas al paquete.

La decisión pendiente para el mapa es elegir **release fija con actualización mediante `add`**, o **rama seguida mediante `check/update`**. Las preferencias ya expresadas —actualización explícita revisable, dos agentes y copia upstream adaptada— encajan mejor con la primera. Este informe aporta el contrato técnico necesario para resolver esa decisión sin asumir que `@tag` o `update` hacen lo que no hacen.
